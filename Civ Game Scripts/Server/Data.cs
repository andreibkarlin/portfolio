using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System.Linq; //For the shuffle

/* This script stores the data of all of the tiles on the map, and all of the troops.
 * It has client sided data (such as queued movement of troops), as well as server sided data
 * such as the ownership of tiles and if they have a troop on them.
 * This includes the Move command, where the client side will tell the server
 * to move a troop, which will processed here. 
 * That way client and server is seperated when the game is made multiplayer.
 */
public static class Data
{
    //Map => Country (0 for none, 1 for red, 2 for blue), Has Troop?
    //Mapc => List of client sided attributes, like if a tile is selected.
    //Troops => Position: Country, Type, Equipment, HP, MP.
        //ADD: ID? Max HP?
    //Troopc => Position: Pathfinding? | Destination, Directions...
    public static MapTile[] Map;
    public static List<Troop> Troops = new();
    public static List<Country> Countries = new();
    public static List<Building> Buildings = new();
    public static Country country;

    public static void Awake() //Initialization of variables.
    {
        //Reset IDs
        Country.currentID = 0;
        Troop.currentID = 0;
        MapTile.currentPosition = 0;
        
        Map = new MapTile[576];
        for (int i = 0; i < 576; i++) Map[i] = new();
        for (int i = 0; i < 576; i++) TileScript.MapC[i] = new List<string> { null }; //Help initialize MapC. TEMPORARY.
        //countries = new() { new("Oceania", Color.gray), new("Eurasia", Color.red), new("Eastasia", Color.yellow) };
        for (int i = 0; i < 2; i++) Countries.Add(new(i));
        country = Countries[0];
        Object.FindObjectOfType<UIHandler>().UpdateCountry();

        //Reset static variables from other scripts
        TroopClient.TroopC = new();
    }
    public static void GenerateMap() //For the sake of the current build, it spawns 6 troops in random positions.
    {
        int mapSize = 24;
        //Add water
        float randomX = Random.Range(-100000f, 100000f); //Arbitrarily large numbers (100k)
        float randomY = Random.Range(-100000f, 100000f);
        float perlinReduction = 5; //How large the randomness is.
        float waterCutOff = 0.25f; // How high is the water level? (0-1)
        for (int col = 0; col < mapSize; col++)
            for (int row = 0; row < mapSize; row++) {
                float edgeDistance = Mathf.Min(Mathf.Min(row, mapSize - 1 - row), Mathf.Min(col, mapSize - 1 - col));
                float perlinNoise = Mathf.PerlinNoise(randomX + col / perlinReduction, randomY + row / perlinReduction);
                perlinNoise *= Mathf.Sqrt(2 * edgeDistance / mapSize);
                if (perlinNoise <= waterCutOff) {
                    Map[col + row * mapSize].isWater = true;
                }
            }
        //Shuffle countries
        Countries = Countries.OrderBy(x => Random.value).ToList();
        //Create data for each country
        for (int i = 0; i < Countries.Count; i++) {
            int tilePos = Random.Range(0, mapSize * mapSize);
            MapTile tile = Map[tilePos];
            if (!tile.isWater && !tile.HasCity()
            && (tile.country == null || tile.country == Countries[i])) {
                Country country = tile.country = Countries[i];
                List<Pop> pops = new() { new Pop(), new Pop(), new Pop() };
                
                City city = new(tile);
                city.pops = new(pops);
                Buildings.Add(city);
                tile.building = city;

                Troop troop = SpawnTroop(city, tile, tile.country);
                troop.HP = 100;
                troop.MP = 4;
                troop.pop = pops[2];
                TileScript.MapC[tilePos].Add(null); //Update tile. TEMPORARY?
                
                //Add country data
                country.troops.Add(troop);
                country.buildings.Add(city);
                country.tiles.Add(tile);
                country.pops = pops;
            } else i--; //Try again.
        }

    }
    public static MoveResult Move(Troop troop, Direction direction) //Move a troop one space over.
    {
        int cityHealthToLosePops = 50;
        int tile = troop.position;
        int resultPos = Pathfinding.Adjacent(tile, direction);
        if (resultPos < 0) return MoveResult.invalid;
        MapTile result = Map[Pathfinding.Adjacent(tile, direction)];
        if (result.position >= 0 && !(result.HasTroop() || (result.HasCity() && result.country != troop.country))) {
            float movementCost = result.MovementCost(troop);
            if (troop.MP >= movementCost && movementCost > 0) {
                troop.MP -= movementCost;
                result.troop = troop;
                Map[tile].troop = null;
                troop.position = result.position;
                troop.tile = result;
                ClaimTile(result, troop.country);
                return MoveResult.success; //Successfully moved
            }
        //If there is an enemy troop or city in the tile, engage in combat.
        } else if ((result.HasTroop() || result.HasCity()) && troop.country != result.country && troop.MP >= 1) {
            BattleSimulator battle = SimulateBattle(troop, result);
            MoveResult output = MoveResult.invalid;
            if (battle.result == BattleResult.loss || battle.result == BattleResult.sacrifice) {
                Direction runAwayDirection = Pathfinding.FlipDirection(direction);
                int runAway = Pathfinding.Adjacent(tile, runAwayDirection);
                if (runAway >= 0 && !Map[runAway].HasTroop() && (!Map[runAway].HasCity() || Map[runAway].country == troop.country) && !Map[tile].HasCity()) {
                    MoveResult retreat = Move(troop, runAwayDirection);
                    if (retreat == MoveResult.success)
                        return MoveResult.mutiny;
                } //Remove the dead attacking troop
                KillTroop(troop);
                output = MoveResult.battleLoss;
            } 
            if (new BattleResult[] { BattleResult.troopWin, BattleResult.garrisonWin, BattleResult.cityAndGarrisonWin, BattleResult.sacrifice }
            .Contains(battle.result)) {
                Troop troop2 = result.troop;
                //The defending troop will try to escape if it can and has already fought a battle recently, and it isn't in a city.
                int runAway = Pathfinding.Adjacent(troop2.position, direction);
                if (troop2.timeSinceEngagement <= 1 &&
                    runAway >= 0 && !Map[runAway].HasTroop() && (!Map[runAway].HasCity() || Map[runAway].country == troop2.country) && !result.HasCity()) {
                    MoveResult retreat = Move(troop2, direction);
                    if (retreat == MoveResult.success && !Map[tile].HasCity()) {
                        result.troop = troop;
                        Map[tile].troop = null;
                        troop.position = result.position;
                        troop.tile = result;
                        ClaimTile(result, troop.country);
                        troop.MP -= 1;
                        return MoveResult.advance;
                }} //Remove the dead defending troop
                KillTroop(troop2);
                if (!result.HasCity()) output = MoveResult.battleWin;
            }
            if (battle.result == BattleResult.cityWin || battle.result == BattleResult.cityAndGarrisonWin) {
                City city = (City)result.building;
                city.HP = 1;
                ClaimTile(result, troop.country);
                output = MoveResult.battleWin;
            }
            if (battle.result == BattleResult.battle) output = MoveResult.battle;
            if (battle.result == BattleResult.invalid) return MoveResult.invalid;
            //Process the results of the battle.
            troop.MP -= 1; //Lower movement points.
            troop.timeSinceEngagement = 0;
            troop.HP = battle.troop1HP;
            if (result.HasTroop()) {
                Troop troop2 = result.troop;
                troop2.timeSinceEngagement = 0;
                troop2.HP = battle.troop2HP;
            }
            if (result.HasCity() && result.country != troop.country) {
                City city = (City)result.building;
                city.HP = battle.cityHP;
                if (city.HP < cityHealthToLosePops && city.pops.Count > 0) {
                    Pop pop = city.pops.Last();
                    city.pops.Remove(pop);
                    city.tile.country.pops.Remove(pop);
                }
            }
            return output;
        }
        return MoveResult.invalid; //Invalid order
    }
    //Simulate a battle, without actually doing anything. Troop1 attacks troop2.
    public static BattleSimulator SimulateBattle(Troop troop, MapTile tile)
    {
        //Should be based on type and equipment, but that hasn't been added.
        BattleSimulator output = new();
        int troopATK = troop.Attack();
        int tileATK = 0;
        if (tile.HasTroop()) {
            tileATK += tile.troop.Attack();
            output.troop2HP = tile.troop.HP;
        } else output.troop2HP = -1;
        if (tile.HasCity()) {
            City city = (City)tile.building;
            tileATK += city.Attack();
            output.cityHP = city.HP;
        } else output.cityHP = -1;

        output.troop1HP = troop.HP;
        output.result = BattleResult.battle;
        int attack = troopATK - (int)Mathf.Ceil(tileATK / 4f);
        int defense = tileATK - (int)Mathf.Ceil(troopATK / 4f);
        //The attacker is processed first. If a troop is on the tile, it is attacked first.
        if (tile.HasTroop() && attack > 0) {
            output.troop2HP = tile.troop.HP - attack;
            if (output.troop2HP <= 0) { //Defending troop dies
                if (tile.HasCity()) { 
                    output.result = BattleResult.garrisonWin; //The city remains.
                    defense = tile.building.Attack() - (int)Mathf.Ceil(troopATK / 4f); //The defending troop no longer can attack.
                    attack = -output.troop2HP; //Some attack power is still left.
                } else { //The battle is won.
                    output.result = BattleResult.troopWin;
                    return output;
                }
            } else attack = 0;
        }
        if (tile.HasCity() && attack > 0) {
            City city = (City)tile.building;
            output.cityHP = city.HP - attack;
            if (output.cityHP <= 0) { //City is captured
                output.cityHP = 0;
                output.result = (output.result == BattleResult.garrisonWin) ? BattleResult.cityAndGarrisonWin : BattleResult.cityWin;
                return output;
            }
        }
        //Now the defender is processed.
        if (defense > 0) {
            output.troop1HP -= defense;
            if (output.troop1HP <= 0) { //Attacking troop dies
                output.result = (output.result == BattleResult.garrisonWin) ? BattleResult.sacrifice : BattleResult.loss;
                return output;
            }
        }
        return output; //Returns "battle" by default.
    }
    public static GameResources Income(Country country) {
        int troops = country.troops.Count;
        int population = country.pops.Count;
        GameResources income = new(food: population * -5 + (country.tiles.Count - country.buildings.Count) * 2, gold: troops * -2);
        foreach (Building building in country.buildings) {
            income.Add(building.Income());
        }
        return income;
    }
    public static void NextTurn() {
        foreach (Troop troop in Troops) {
            troop.MP = 4; //Replenish movement points
            troop.Heal();
            troop.timeSinceEngagement++;
        }
        foreach (Country country in Countries)        
            country.resources.Add(Income(country));
        foreach (Building building in Buildings)
        {
            if (building is City city) {
                city.GrowPop();
                city.Heal();
            }
        }
    }
    public static Troop SpawnTroop(City city, MapTile tile, Country country) {
        if (!tile.HasTroop() && !tile.isWater) {
            ///TODO: Process tile swap, whatever
            tile.country = country;
            Troop newTroop = new(country, tile);
            Troops.Add(newTroop);
            tile.troop = newTroop;
            country.troops.Add(newTroop);
            TileScript.MapC[tile.position].Add(null); //Update tile. TEMPORARY?
            TroopClient.TroopC.Add(newTroop, new(newTroop)); //Add client data (temporary)
            Pop pop = city.pops.Last();
            newTroop.pop = pop;
            city.pops.Remove(pop);
            return newTroop;
        } return null;
    }
    public static void ClaimTile(MapTile tile, Country country) {
        if (tile.country != null) tile.country.tiles.Remove(tile);
        if (tile.HasBuilding()) {
            country.buildings.Add(tile.building);
            tile.country.buildings.Remove(tile.building);
        }
        tile.country = country;
        country.tiles.Add(tile);
    }
    public static void KillTroop(Troop troop) {
        Troops.Remove(troop);
        troop.tile.troop = null;
        troop.exists = false;
        troop.country.troops.Remove(troop);
        troop.country.pops.Remove(troop.pop);
    }
    public enum MoveResult { invalid = -1, success, battle, battleWin, battleLoss, mutiny, advance }
    public enum BattleResult { invalid = -1, battle, troopWin, loss, garrisonWin, cityWin, cityAndGarrisonWin, sacrifice }
    public struct BattleSimulator { public int troop1HP; public int troop2HP; public int cityHP; public BattleResult result; }
}
