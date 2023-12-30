using System.Collections;
using System.Collections.Generic;
using UnityEngine;
//Handles paths for troops in move mode or attack mode.
public static class TroopPaths
{
    static int lastTileHover;
    static List<Direction> path;
    static List<Direction> directions;

    public static void ResetVars()
    {
        lastTileHover = -1;
        path = new();
        directions = new();
    }
    //Render the move mode path of a troop.
    public static void RenderMovePath(int tileHover, Troop troop, ClientTroopObject troopC, PathRender pathrender)
    {
        if (lastTileHover != tileHover) { //Recalculate path
            lastTileHover = tileHover;
            path = Pathfinding.Pathfind(troop,
                (troopC.destinations.Count > 0) ? troopC.destinations[^1] : troop.position, tileHover);
            directions = troopC.GenerateDirections();
            if (path != null && Data.Map[tileHover].MovementCost(troop) >= 0) directions.AddRange(path);
        }
        pathrender.PathRendering(troop.position, directions);
    }
    //Process the intput of move mode when a tile is selected.
    public static void MoveSelect(ClientTroopObject troopC)
    {
        troopC.DisableCombatMode();
        troopC.destinations.Add(lastTileHover);
        troopC.path.Add(new());
        troopC.pathfinding = false;
        try { troopC.path[^1].AddRange(path); } catch { }
    }
    public static void RenderAttackPath(int tileHover, Troop troop, PathRender pathrender)
    {
        if (lastTileHover != tileHover)
        { //Recalculate path
            lastTileHover = tileHover;
            directions = Pathfinding.Pathfind(troop, troop.position, tileHover, true);
        }
        if (directions != null) pathrender.PathRendering(troop.position, directions);
        else pathrender.PathRendering();
        if (Data.Map[tileHover].HasTroop() || Data.Map[tileHover].HasCity()) pathrender.PathRenderColor(1);
    }
    public static void AttackSelect(ClientTroopObject troopC)
    {
        troopC.combatMode = true;
        MapTile tile = Data.Map[lastTileHover];
        if (tile.HasCity()) troopC.target = (City)Data.Map[lastTileHover].building;
        else troopC.target = Data.Map[lastTileHover].troop;
        troopC.combatPath = directions;
        troopC.targetLastLocation = lastTileHover;
    }
    public static void AttackTileSelect(ClientTroopObject troopC)
    {
        troopC.DisableCombatMode();
        troopC.destinations = new() { lastTileHover };
        troopC.path = new() { new() };
        try { troopC.path[0].AddRange(directions); } catch { }
    }
}
