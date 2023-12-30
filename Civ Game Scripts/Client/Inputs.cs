using System.Collections;
using System.Collections.Generic;
using UnityEngine;
//Handles user inputs.
public static class Inputs
{
    static int tileHover;
    static int selectedTile;
    static string selected; //The type of thing that is selected.
    static string selectMode; //The mode of selection.

    static Controls controls;
    static TabScript tabs;
    static PathRender pathrender;
    static UIHandler UIHandler;

    public static void ResetVars()
    {
        tileHover = -1;
        selectedTile = -1;
        selected = null;
        selectMode = "Normal";
        controls = new();
        tabs = Object.FindObjectOfType<TabScript>();
        pathrender = Object.FindObjectOfType<PathRender>();
        UIHandler = Object.FindObjectOfType<UIHandler>();
        TroopPaths.ResetVars();
    }

    public static void HandleInputs()
    {
        //See if controls are active (Check if the game is paused or the console is open).
        if (DebugConsole.showConsole || PauseMenu.IsPaused) controls.Game.Disable();
        else controls.Game.Enable();
        
        //Process any data based on what is selected.
        if (selectedTile >= 0) {
            if (selected == "Troop")
            {
                Troop troop = Data.Map[selectedTile].troop;
                try { 
                    ClientTroopObject troopC = TroopClient.TroopC[troop]; 
                    //Render pathrendering
                    if (selectedTile >= 0 && troop.country == Data.country && selectMode != "Attack") 
                        pathrender.PathRendering(selectedTile, troopC.GenerateDirections(), troopC.combatMode ? 1 : 0);
                    //Moving a troop.
                    if (tileHover >= 0) {
                        if (controls.Game.Move.triggered && troop.country == Data.country) {
                            troopC.DisableCombatMode();
                            troopC.destinations.Add(tileHover);
                            troopC.path.Add(new());
                            //Do pathfinding
                            int start = (troopC.destinations.Count > 1) ? troopC.destinations[^2] : selectedTile;
                            List <Direction> pathfind = Pathfinding.Pathfind(troop, start, tileHover);
                            if (pathfind != null) troopC.path[^1].AddRange(pathfind);
                        }
                        //Handle troop paths.
                        if (selectMode == "Move")
                            TroopPaths.RenderMovePath(tileHover, troop, troopC, pathrender);
                    if (selectMode == "Attack")
                        TroopPaths.RenderAttackPath(tileHover, troop, pathrender);
                    }
                } catch { Deselect(); }
            }
            //else if (selected == "Building") { }
        }

        //Process any inputs on tiles.
        if (tileHover >= 0) {
            MapTile tile = Data.Map[tileHover];
            //Process clicks based on the selectMode.
            if (controls.Game.Select.triggered) {
                /*//Holding down clicking
                else if (controls.Game.Move.IsPressed() && selectedTile >= 0 && Data.Map[TileHover][1] == 0
                && Data.Troops[selectedTile][0] == Data.country) {
                    PathRender.PathRendering(selectedTile, Pathfinding.Pathfind(Data.country, selectedTile, TileHover));
                }*/
                switch (selectMode) {
                    case "Normal":
                        switch (tabs.selectedTab) {
                            case "Troops":
                                if (tile.HasTroop()) {
                                    if (selectedTile == tileHover && selected == "Troop") DeselectTile();
                                    else Select(tileHover, "Troop");
                                }
                                break;
                            case "Land":
                                if (tile.HasBuilding()) {
                                    if (selectedTile == tileHover && selected == "Building") DeselectTile();
                                    else Select(tileHover, "Building");
                                }
                                break;
                            default:
                                if (tile.HasCity()) {
                                    if (selectedTile == tileHover && selected == "Building") { //If the city is already selected
                                        if (tile.HasTroop()) Select(tileHover, "Troop"); //Select the troop.
                                        else DeselectTile(); //Deselect the city.
                                    } else {
                                        if (selected == "Troop" && selectedTile != tileHover && tile.HasTroop()) Select(tileHover, "Troop"); //Select the troop.
                                        else Select(tileHover, "Building"); //Select the city.
                                    }
                                } else if (tile.HasTroop()) {
                                    if (selectedTile == tileHover && selected == "Troop") { //If the troop is already selected
                                        if (tile.HasBuilding()) Select(tileHover, "Building"); //Select the building.
                                        else DeselectTile(); //Deselect the troop.
                                    } else Select(tileHover, "Troop"); //Select the troop.
                                } else if (tile.HasBuilding()) {
                                    if (selectedTile == tileHover && selected == "Building") DeselectTile(); //Deselect the building.
                                    else Select(selectedTile, "Building"); //Select the building.
                                }
                                break;
                        }
                        break;
                    case "Move":
                        Troop troop = Data.Map[selectedTile].troop;
                        ClientTroopObject troopC = TroopClient.TroopC[troop];
                        TroopPaths.RenderMovePath(tileHover, troop, troopC, pathrender);
                        TroopPaths.MoveSelect(troopC);
                        Deselect();
                        break;
                    case "Attack":
                        troop = Data.Map[selectedTile].troop;
                        troopC = TroopClient.TroopC[troop];
                        TroopPaths.RenderAttackPath(tileHover, troop, pathrender);
                        if ((tile.HasTroop() || tile.HasCity()) && selectedTile != tileHover)
                            TroopPaths.AttackSelect(troopC);
                        else TroopPaths.AttackTileSelect(troopC);
                        Deselect();
                        break;
                    case "Spawn":
                        if (tile.isWater || tile.HasTroop() || Pathfinding.Distance(selectedTile, tileHover) > 1) break; //Invalid tile.
                        City city = (City)Data.Map[selectedTile].building;
                        if (city.pops.Count == 0) break;
                        if (!city.tile.country.resources.Spend(new(gold: 20))) break;
                        //When diplomacy is added, there should be a check to see if you have access (at war or it's yours)
                        tile.country = Data.Map[selectedTile].country; 
                        Data.SpawnTroop(city, tile, tile.country);
                        Deselect();
                        break;
                }
            }
        }
        //Process other inputs.
        if (controls.Game.Deselect.triggered && selectedTile >= 0) Deselect();
        if (controls.Game.NextTurn.triggered) ButtonInput("nextTurn");
    }

    static void Select(int tile, string mode)
    {
        if (selectedTile >= 0) {
            TileScript.MapC[selectedTile].Add("Deselect");
            if (selected == "Troop") pathrender.PathRendering(); //Reset pathrendering.
        }
        selectedTile = tile;
        TileScript.MapC[selectedTile].Add("Select");
        TileScript.MapC[selectedTile].Add(mode);
        selected = mode;
        ///WORK ON THIS:
        //if (tabs.selectedTab != "Troops") tabs.SelectTab("Troops");
    }
    static void DeselectTile()
    {
        TileScript.MapC[selectedTile].Add("Deselect");
        selectedTile = -1;
        if (selected == "Troop") pathrender.PathRendering(); //Reset pathrendering.
        selected = null;
    }
    public static bool TransferSelectedTile(int start, int end) {
        if (selectedTile == start && start >= 0) {
            selectedTile = end;
            TileScript.MapC[start].Add("Deselect");
            TileScript.MapC[end].Add("Select");
            TileScript.MapC[end].Add("Troop");
            return true;
        } return false;
    }
    public static void Deselect(bool recursive = false)
    {
        if (selectMode == "Normal") {
            if (selected != null)
                DeselectTile();
            else if (tabs.selectedTab != "None") tabs.SelectTab(tabs.selectedTab); //Deselect tab
        } else if (selectMode == "Move" || selectMode == "Attack") {
            UIHandler.SetSelectMode(null);
            selectMode = "Normal";
            TroopPaths.ResetVars();
            pathrender.PathRendering();
            if (recursive) Deselect();
        } else if (selectMode == "Spawn") {
            UIHandler.SetSelectMode(null);
            selectMode = "Normal";
            if (recursive) Deselect();
        }
    }
    public static void ButtonInput(string type)
    {
        if (DebugConsole.showConsole) return;
        //This should not be with the client code! But for now it'll do. [TEMPORARY FEATURE]
        if (type == "nextTurn") {
            if (SettingsMenu.switchCountries) {
                int currentCountry = Data.country.ID;
                currentCountry += 1;
                if (currentCountry == Country.currentID) {
                    currentCountry = 0;
                    Data.NextTurn();
                }
                Data.country = Data.Countries[currentCountry];
                UIHandler.UpdateCountry();
                Deselect(true);
            } else Data.NextTurn();
            return;
        }
        MapTile tile = Data.Map[selectedTile];
        if (selected == "Troop") {
            Troop troop = tile.troop;
            ClientTroopObject troopC = TroopClient.TroopC[troop];
            switch (type) {
                case "deleteTroop":
                    if (Data.country == troop.country) {
                        Data.KillTroop(troop);
                        Deselect(true);
                    }
                    break;
                case "moveMode":
                    if (Data.country != troop.country) break;
                    if (selectMode != "Move") {
                        selectMode = "Move";
                        UIHandler.SetSelectMode("Move Mode");
                    } else Deselect();
                    break;
                case "attackMode":
                    if (selectMode != "Attack") {
                        selectMode = "Attack";
                        UIHandler.SetSelectMode("Attack Mode");
                    } else Deselect();
                    break;
                case "clearQueue":
                    if (Data.country == troop.country) {
                        troopC.destinations = new();
                        troopC.path = new();
                        if (troopC.combatMode) troopC.DisableCombatMode();
                    }
                    break;
                case "removeLast":
                    if (Data.country == troop.country) {
                        if (troopC.destinations.Count > 0) {
                            troopC.destinations.RemoveAt(troopC.destinations.Count - 1);
                            troopC.path.RemoveAt(troopC.path.Count - 1);
                        } 
                        if (troopC.combatMode) troopC.DisableCombatMode();
                    }
                    break;
            }
        } else if (selected == "Building") {
            Building building = Data.Map[selectedTile].building;
            if (building is City) {
                switch (type) {
                    case "spawnTroop":
                        if (Data.country != tile.country) break;
                        if (selectMode != "Spawn") {
                            selectMode = "Spawn";
                            UIHandler.SetSelectMode("Spawn Troop");
                        }
                        else Deselect();
                        break;
                }
            }
        }
    }
    public static void SetHover(int hover) { tileHover = hover; }
    public static int GetSelectedTile() { return selectedTile; }
    public static string GetSelectedType() { return selected; }
}