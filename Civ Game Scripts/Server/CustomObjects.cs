using System.Collections;
using System.Collections.Generic;
using UnityEngine;
public class Country
{
    public static int currentID;
    public readonly int ID;

    public string name; //The country's name.
    public Color color; //The country's color.
    public GameResources resources; //The country's resources.

    // Lists of things that the country possesses.
    public List<Troop> troops = new();
    public List<Building> buildings = new();
    public List<MapTile> tiles = new();
    public List<Pop> pops = new();

    public Country() { 
        ID = currentID++;
        resources = new(gold: 80, food: 50, wood: 40);
    }
    public Country(string name, Color color) : this()
    {
        this.name = name;
        this.color = color;
    }
    public Country(int preset) : this() 
    {
        switch (preset) {
            case 0:
                name = "Red";
                color = Color.red;
            break; case 1:
                name = "Blue";
                color = Color.blue;
            break; case 2:
                name = "Green";
                color = Color.green;
            break; case 3:
                name = "Yellow";
                color = Color.yellow;
            break; case 4:
                name = "Pink";
                color = Color.magenta;
            break;
        }
        //color = Color.Lerp(color, Color.gray, 0.5f);
    }
    public bool Exists() { return buildings.Count > 0; }
}
public class Troop
{
    public static int currentID;
    public readonly int ID;

    public bool exists = true;
    public readonly Country country;
    public int position;
    public MapTile tile;
    public Pop pop;

    public float MP; //Movement Points. Out of 4. Can be subdivided into bits of 0.5
    public int HP; //Hit Points. Out of 100.
    public int type; //Does nothing for now. Type is always 0.
    public int equipment; //Does nothing for now. Equipment is always 0.

    public int timeSinceEngagement; //Turns since the troop was last in a battle. Only matters if it's 0 or 1.

    public Troop(Country Country, MapTile tile)
    {
        ID = currentID++;
        country = Country;
        this.tile = tile;
        position = tile.position;
        HP = 50;
        MP = 0;
        timeSinceEngagement = 2;
    }
    public int Attack() { return 50; }
    public int MaxHP() { return 100; }
    public void Heal() {
        if (timeSinceEngagement > 0 || tile.HasCity()) {
            if (HP < MaxHP()) {
                HP += MaxHP() / 4;
                if (HP > MaxHP()) HP = MaxHP();
            }
        }
    }
    public string Status() {
        if (tile.HasCity()) return "Garrisoned";
        if (timeSinceEngagement == 0) return "Battle";
        if (timeSinceEngagement == 1) return "Alert";
        return "Normal";
    }
}
public class MapTile
{
    public static int currentPosition;
    public readonly int position; //The position of the tile, immutable.

    public Country country; //The country owning the tile, or null if unclaimed.
    public Troop troop; //The troop on the tile, or null if there is none.
    public Building building;
    public bool isWater;
    public MapTile() { position = currentPosition++; }
    public float MovementCost(Troop troop)
    {
        if (this.troop != null) {
            if (this.troop.country == troop.country) return -1; //Not possible
            else return 0; //Immovable, but a valid tile.
        }
        if (isWater) return -1; //Not possible to move on
        else if (troop.country == country) return 0.5f;
        else return 1;
    }
    public bool HasTroop() { return troop != null; }
    public bool HasBuilding() { return building != null; }
    public bool HasCity() {
        //if (building == null) return false;
        return building is City;
    }
}
public class Building
{
    public static int currentID;
    public readonly int ID;
    public readonly MapTile tile;
    public List<Pop> pops; //Population of the building (workers).
    public int capacity; //Max number of workers.
    public BuildingData type;
    public Building(string building, MapTile tile)
    {
        ID = currentID++;
        type = new(building);
        this.tile = tile;
        capacity = type.Capacity();
        pops = new();
    }
    public int Attack() { return 5 * pops.Count; }
    public virtual GameResources Income() {
        if (pops.Count == capacity) return type.Income();
        else return new();
    }
}
public class City : Building
{
    public int HP;
    public City(MapTile tile) : base("city", tile) {
        HP = 20; //Temporary
    }
    public void GrowPop()
    {
        int pairs = pops.Count / 2;
        for (int i = 0; i < pairs; i++) if (pops.Count < capacity) {
            Pop pop = new Pop();
            pops.Add(pop);
            tile.country.pops.Add(pop);
        }
    }
    public int MaxHP() {
        return pops.Count * 15;
    }
    public void Heal() {
        if (HP < MaxHP() && pops.Count > 0) {
            HP += MaxHP() / 4;
            if (HP > MaxHP()) HP = MaxHP();
        }
    }
    public override GameResources Income() { return type.Income(); }
}
public class GameResources
{
    public static List<string> resourceTypes = new() { "gold", "food", "wood", "stone" };
    public Dictionary<string, int> resources = new();

    public GameResources() { }
    public GameResources(Dictionary<string, int> resources)
    {
        this.resources = resources;
    }
    public GameResources(int gold = 0, int food = 0, int wood = 0, int stone = 0) {
        if (gold != 0) resources["gold"] = gold;
        if (food != 0) resources["food"] = food;
        if (wood != 0) resources["wood"] = wood;
        if (stone != 0) resources["stone"] = stone;
    }

    public bool CanAfford(GameResources cost) {
        foreach(KeyValuePair<string, int> pair in cost.resources) {
            if (!resources.ContainsKey(pair.Key) || pair.Value > resources[pair.Key]) return false;
        }
        return true;
    }
    public bool Spend(GameResources cost) {
        if (!CanAfford(cost)) return false;
        foreach(KeyValuePair<string, int> pair in cost.resources) {
            resources[pair.Key] -= pair.Value;
        }
        return true;
    }
    public void Add(GameResources income) {
        foreach (KeyValuePair<string, int> pair in income.resources) {
            resources[pair.Key] += pair.Value;
        }
    }
    public int Get(string resource) {
        if (!resources.ContainsKey(resource)) return 0;
        else return resources[resource];
    }
}
public class BuildingData
{
    static List<string> types = new() { "city" };
    struct BuildingDataObject
    {
        public GameResources cost;
        public GameResources income;
        public int capacity;
        public BuildingDataObject(GameResources cost, GameResources income, int capacity) {
            this.cost = cost;
            this.income = income;
            this.capacity = capacity;
        }
    }
    static Dictionary<string, BuildingDataObject> buildings = new() {
        { "city", new(cost: new(gold: 100), income: new(gold: 12), capacity: 8) }
    };

    public string type;
    public BuildingData(string type)
    {
        if (types.Contains(type)) this.type = type;
        else throw new System.ArgumentException("Invalid building type.");
    }
    public GameResources Cost() { return buildings[type].cost; }
    public GameResources Income() { return buildings[type].income; }
    public int Capacity() { return buildings[type].capacity; }
}
public class Pop
{
    public static int currentID;
    public readonly int ID;
    public Pop()
    {
        ID = currentID++;
    }
}
public enum Direction : int { east, north, west, south }