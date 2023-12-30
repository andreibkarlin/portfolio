using System.Collections;
using System.Collections.Generic;
using UnityEngine;
/// <summary>
/// Code to handle client sided aspects of troop momvement
/// </summary>
public static class TroopClient
{
    public static Dictionary<Troop, ClientTroopObject> TroopC = new();
    //Called by main.
    public static void HandleTroopMovements()
    {
        List<TroopOrder> orders = new();
        Dictionary<Troop, ClientTroopObject> CleanTroopC = new();
        foreach (var dict in TroopC)
            if (dict.Value.Troop.exists)
                CleanTroopC.Add(dict.Key, dict.Value);
        TroopC = CleanTroopC;
        //TroopC = TroopC.Where(troopC => !troopC.Value.Troop.exists).ToDictionary(d => d.Key, d => d.Value);
        //TroopC.RemoveAll(troopC => !troopC.Troop.exists);
        foreach (var dict in TroopC) {
            ClientTroopObject troopC = dict.Value;
            Troop troop = dict.Key;
            int position = troop.position;
            //If there is pathfinding to be done, then add the directions.
            while (troopC.pathfinding) {
                for (int goal = 0; goal < troopC.destinations.Count; goal++) {
                    List<Direction> directions;
                    int oldPos = (goal == 0) ? position : troopC.destinations[goal - 1];
                    directions = Pathfinding.Pathfind(troop, oldPos, troopC.destinations[goal]);
                    if (directions != null) {
                        float costNew = Pathfinding.PathCost(troop, oldPos, directions);
                        float costOld = Pathfinding.PathCost(troop, oldPos, troopC.path[goal]);
                        if (costNew < costOld) troopC.path[goal] = directions;
                        troopC.pathfinding = false; //Done pathfinding.
                    //If the pathfinding is invalid, remove the invalid instruction.
                    } else if (troopC.destinations[goal] == troop.position) { 
                        troopC.destinations.RemoveAt(goal);
                        troopC.path.RemoveAt(goal);
                        if (troopC.destinations.Count > 1) troopC.pathfinding = true;
                        else troopC.pathfinding = false;
                        goal--; //Accounting for how the indexes changed.
                    }
                }
            }
            //If there are directions to be followed:
            if (troopC.destinations.Count > 0 && !troopC.combatMode) {
                if (troopC.path[0].Count == 0) {
                    troopC.destinations.RemoveAt(0);
                    troopC.path.RemoveAt(0);
                    continue;
                }
                int goal = Pathfinding.Adjacent(position, troopC.path[0][0]);
                MapTile tile = Data.Map[goal];
                //If the movement is valid
                if (goal >= 0 && !tile.isWater &&
                   (!tile.HasTroop() || (tile.HasTroop() && goal == troopC.destinations[0] && tile.troop.country != troop.country))) {
                    //If the troop has movement points
                    if ((troop.MP >= tile.MovementCost(troop) && !tile.HasTroop()) || (troop.MP >= 1 && tile.HasTroop())) {
                        //Make a list of orders to follow, remove the relevant orders from the client data.
                        orders.Add(new(troop, troopC.path[0][0]));
                    }
                } else { //If the goal is invalid, cancel orders, try to find a new path.
                    troopC.path[0] = new();
                    List<Direction> directions = Pathfinding.Pathfind(troop, position, troopC.destinations[0]);
                    if (directions == null) {
                        troopC.path = new() { new() };
                        troopC.destinations = new();
                        troopC.pathfinding = false;
                    } else { 
                        troopC.path[0].AddRange(directions);
                        if (Pathfinding.Adjacent(position, troopC.path[0][0]) == goal //If the path still isn't valid
                            && !(goal >= 0 && !tile.isWater && (!tile.HasTroop() || tile.troop.country != troop.country)))
                            troopC.RemoveFirstDestination();
                    }
                }
            } else if (troopC.combatMode) {
                if (!troopC.TargetExists()) { //If the troop is dead, you are done. Go to where it was.
                    troopC.target = null;
                    troopC.combatMode = false;
                    troopC.combatPath = new();
                    troopC.destinations.Add(troopC.targetLastLocation);
                    troopC.path = new() { new() };
                    troopC.targetLastLocation = -1;
                    continue;
                } 
                if (troopC.TargetPos() != troopC.targetLastLocation) {
                    troopC.combatPath = Pathfinding.Pathfind(troop, position, troopC.TargetPos(), true);
                    troopC.targetLastLocation = troopC.TargetPos();
                }
                if (troopC.combatPath.Count == 0) {
                    List<Direction> path = Pathfinding.Pathfind(troop, troop.position, troopC.TargetPos(), true);
                    if (path != null) troopC.combatPath = path;
                    else {
                        troopC.combatMode = false;
                        troopC.target = null;
                        troopC.targetLastLocation = -1;
                        continue;
                    }
                }
                int goal = Pathfinding.Adjacent(position, troopC.combatPath[0]);
                float movementCost = Data.Map[goal].MovementCost(troop);
                if ((troop.MP >= movementCost && movementCost > 0) || (Data.Map[goal].HasTroop() && troop.MP >= 1)) {
                    orders.Add(new(troop, troopC.combatPath[0]));
                }
            }
        }
        //Sends out orders to the server.
        if (orders != null) for (int order = 0; order < orders.Count; order++) {
            Troop troop = orders[order].troop;
            Direction direction = orders[order].direction;
            //Handle the server sided aspects of movement.
            Data.MoveResult result;
            result = Data.Move(troop, direction);
            //Update tiles
            TileScript.MapC[troop.position].Add(null);
            TileScript.MapC[Pathfinding.Adjacent(troop.position, direction)].Add(null);


            if (result == Data.MoveResult.success || result == Data.MoveResult.advance) //If it successfully moved:
                ClientMovement(troop, direction); //Handle the client sided aspects of movement.
            else if (result == Data.MoveResult.battleLoss)
                Inputs.Deselect(true);
            else if (result == Data.MoveResult.mutiny) {
                ClientMovement(troop, Pathfinding.FlipDirection(direction));
                if (TroopC[troop].combatMode) TroopC[troop].combatPath = new();}
            else if (result == Data.MoveResult.battleWin) 
                if (!troop.tile.HasCity()) order--; //Repeat the order again, unless in a city.
            else if (result == Data.MoveResult.battle) //If there was an inconclusive battle:
                //Because the troop is not at it's destination point but has completed its orders, it must re-pathfind to any extra orders.
                if (TroopC[troop].path.Count > 0) TroopC[troop].path[0] = new();
            else if (result == Data.MoveResult.invalid) //Same logic
                if (TroopC[troop].path.Count > 0) TroopC[troop].path[0] = new();

            if (result != Data.MoveResult.invalid) {
                ClientTroopObject troopC = TroopC[troop];
                troopC.RemoveFirstInstruction();
            }
        }
    }
    public static void ClientMovement(Troop troop, Direction direction)
    {
        int tile = troop.position;
        int cameFrom = Pathfinding.Adjacent(tile, Pathfinding.FlipDirection(direction));
        //Update the relevant tiles. Troop data transfers automatically.
        TileScript.MapC[tile].Add(null);
        TileScript.MapC[cameFrom].Add(null);
        Inputs.TransferSelectedTile(cameFrom, tile); //Transfer the selection.
    }
    public struct TroopOrder { 
        public Troop troop; public Direction direction;
        public TroopOrder(Troop troop, Direction direction) { this.troop = troop; this.direction = direction; }
    }
}

public class ClientTroopObject
{
    public Troop Troop { get; }
    public bool pathfinding;
    public List<int> destinations;
    public List<List<Direction>> path;

    public bool combatMode;
    //public Troop targetTroop;
    public object target;
    public List<Direction> combatPath;
    public int targetLastLocation;
    public ClientTroopObject(Troop Troop) { 
        this.Troop = Troop;
        pathfinding = false;
        destinations = new();
        path = new();
    }
    public List<Direction> GenerateDirections() {
        if (combatMode) {
            if (TargetPos() != targetLastLocation) {
                combatPath = Pathfinding.Pathfind(Troop, Troop.position, TargetPos());
                targetLastLocation = TargetPos();
            }
            return combatPath;
        } else {
            if (path.Count > 0 && path[0].Count == 0) try { path[0].AddRange(Pathfinding.Pathfind(Troop, Troop.position, destinations[0])); } catch { }
            List<Direction> output = new();
            foreach (List<Direction> path in path)
                foreach (Direction direction in path)
                    output.Add(direction);
            return output;
        }
    }
    public void RemoveFirstDestination()
    {
        destinations.RemoveAt(0);
        path.RemoveAt(0);
        if (destinations.Count > 0) pathfinding = true;
        else pathfinding = false;

    }
    public void RemoveFirstInstruction()
    {
        if (combatMode) {
            try { combatPath.RemoveAt(0); } catch { }
        } else {
            try { 
                path[0].RemoveAt(0); 
                if (path[0].Count == 0) RemoveFirstDestination();
            } catch { }
        }
    }
    public void DisableCombatMode() {
        combatMode = false;
        target = null;
        combatPath = new();
        targetLastLocation = -1;
    }
    public int TargetPos()
    {
        if (target is Troop troop) return troop.position;
        if (target is City city) return city.tile.position;
        return -1;
    }
    public bool TargetExists()
    {
        if (target is Troop troop) return troop.exists;
        if (target is City city) return city.tile.country != Troop.country;
        return false;
    }
}