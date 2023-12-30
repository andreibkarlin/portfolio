using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

//This class contains a couple of complicated functions for calculating pathfinding.
static class Pathfinding
{
    //Pathfind using the A* algorithm. 
    public static List<Direction> Pathfind(Troop troop, int start, int end, bool combat = false)
    {
        int mapSize = 24; //Length and width of the map.
        int mapArea = mapSize * 24 + 1;
                                     //These variables below have a value assigned for every tile on the map.
        Direction[] cameFrom = new Direction[mapArea]; //Later used to show where each tile's direction comes from.
                                        //So if pathfinding is O->X, the X tile would have its direction from the left.
        int[] gscore = new int[mapArea]; //Distance of path from start to position.
        int[] hscore = new int[mapArea]; //Calculated distance from position to end.
        int[] fscore = new int[mapArea]; //Sum of g score and h score.
        List<int> openSet = new() { start }; //Set of tiles under consideration to be calculated.
        List<int> closedSet = new() { }; //Set of tiles that have been calculated.
        float[] data = new float[mapArea]; //Imported from map, this is a measure of speed on the tile.
        for (int tile = 0; tile < Data.Map.Length; tile++) {
            data[tile] = Data.Map[tile].MovementCost(troop);
            if (data[tile] == -1) data[tile] = 0;
            if (combat && data[tile] == 0 && Data.Map[tile].HasTroop()) data[tile] = 1;
            if (data[tile] == 0.5) data[tile] = 2;
        }
        data[end] = (troop.country == Data.Map[end].country) ? 2 : 1; //That way, you can attack an enemy or go where one used to be.
        data[troop.position] = (troop.country == Data.Map[end].country) ? 2 : 1; //That way, you go through where the troop used to be.

        if (start == end || data[end] == 0) return null; //Invalid place to pathfind to (either pathfinding to an inaccessible area or to the starting position)
        while (openSet.Count > 0) {
            //Calculate h score and g score of open set (unless already calculated)
            foreach (var tile in openSet) {
                if (fscore[tile] != 0) {
                    int columnTile = tile % mapSize;
                    int columnEnd = end % mapSize;
                    hscore[tile] = Math.Abs(columnTile - columnEnd) + //Distance between columns
                    Math.Abs(tile / mapSize - end / mapSize); //Distance between rows
                    fscore[tile] = gscore[tile] + hscore[tile] * (SettingsMenu.straightPathfinding ? 4 : 1);
                }
            }
            int current = 0; //This gives an error if not set to something. Used to store the selected tile.
            int comparison = 9999; //Arbitrarily high number to start with. Used to store the f score of the selected tile.
            //Find tile with the smallest f score.
            foreach (var tile in openSet) {
                if (fscore[tile] < comparison) {
                    current = tile;
                    comparison = fscore[tile];
                } else if (fscore[tile] == comparison && hscore[tile] < hscore[current]) current = tile; //If the tiles are tied, use the h score.
                else if (fscore[tile] == comparison) if (UnityEngine.Random.value < 0.5) current = tile; //If the tiles are still tied, pick randomly.
                //This would be biased in favor of the later chosen options if there are three or more,
                //as those would have less chances to be randomly replaced. [FIX]   
            }
            //Now process the chosen tile from the open set into the closed set.
            Direction instruction;
            openSet.Remove(current);
            closedSet.Add(current);
            //Data.Map[current][0] = 1; //DEBUG - Visualize the closed set.
            //Goes through the surrounding tiles and adds them to the open set.
            for (int dir = 0; dir < 4; dir++) {
                Direction direction = (Direction)dir;
                int tile = Adjacent(current, direction); //Finds an adjacent tile.
                if (tile >= 0 && data[tile] > 0 && !closedSet.Contains(tile) && !openSet.Contains(tile)) { //Checks if tile is valid. 
                    openSet.Add(tile); //Adds it to the open set.
                    cameFrom[tile] = direction; //Sets the direction it came from
                    if (data[tile] == 2) gscore[tile] = gscore[current] + 1; //Sets g score
                    else gscore[tile] = gscore[current] + 2;
                    fscore[tile] = gscore[tile] + hscore[tile] * (SettingsMenu.straightPathfinding ? 4 : 1);
                    //If it gets to the end, backtrace and reverse engineer the directions. Return the list of directions.
                    if (tile == end) {
                        List<Direction> directions = new();
                        while (true) {
                            instruction = cameFrom[tile];
                            directions.Insert(0, instruction);
                            instruction = FlipDirection(instruction); //Reverses direction.
                            if (Adjacent(tile, instruction) >= 0) tile = Adjacent(tile, instruction);
                            else Debug.Log(tile.ToString() + "cannot be gone to.");
                            if (tile == start) return directions; //Successful output
                        }
                    }
                //If the tile is already in the open set, see if this is a more efficient path to get to that tile.
                } else if (tile >= 0 && data[tile] > 0 && !closedSet.Contains(tile) && openSet.Contains(tile)) {
                    if (gscore[current] < gscore[Adjacent(tile, FlipDirection(cameFrom[tile]))]) { 
                        cameFrom[tile] = direction;
                        if (data[tile] == 2) gscore[tile] = gscore[current] + 1;
                        else gscore[tile] = gscore[current] + 2;
                        fscore[tile] = gscore[tile] + hscore[tile] * (SettingsMenu.straightPathfinding ? 4 : 1);
                    }
                }
            }
        } return null; //No pathfind found
    }
    //Helper function to calculate a tile when given a starting tile and a direction.
    public static int Adjacent(int tile, Direction direction)
    {
        int mapSize = 24;
        if (0 <= tile && tile < (mapSize * mapSize) && 0 <= direction && (int)direction < 4) {
            switch (direction) {
                case Direction.east:
                    if (tile % mapSize == mapSize - 1) return -1;
                    else return tile + 1;
                case Direction.north:
                    if (tile < mapSize) return -1;
                    else return tile - mapSize;
                case Direction.west:
                    if (tile % mapSize == 0) return -1;
                    else return tile - 1;
                case Direction.south:
                    if (tile >= mapSize * (mapSize - 1)) return -1;
                    else return tile + mapSize;
            }
        } 
        return -2; //Invalid inputs.
    }
    public static float PathCost(Troop troop, int start, List<Direction> path)
    {
        float cost = 0;
        int position = start;
        foreach (var direction in path) {
            position = Adjacent(position, direction);
            cost += Data.Map[position].MovementCost(troop);
        }
        return cost;
    }
    public static int Distance(int start, int end) {
        int mapSize = 24;
        int distance = 0;
        distance += Math.Abs(start % mapSize - end % mapSize);
        distance += Math.Abs(start / mapSize - end / mapSize);
        return distance;
    }
    public static Direction FlipDirection(Direction direction) {
        return (Direction)(((int)direction + 2) % 4);
    }
}