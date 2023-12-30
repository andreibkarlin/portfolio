using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

//I used a tutorial for this. This script manages the debug console, which can be accessed with the ` or ~ key. "help" lists the commands.
//Presumably: https://www.youtube.com/watch?v=VzOEM-4A2OM
public class DebugConsole : MonoBehaviour
{
    [HideInInspector] public static bool showConsole;
    [HideInInspector] public static bool debugMode;
    string input;
    string showData;
    Controls controls;
    string lastCommand;

    public List<object> commandList;
    public static DebugCommand help;
    //public static DebugCommand<List<int>> edit_map;
    public static DebugCommand<List<int>> edit_mapc;
    public static DebugCommand<int> get_map;
    public static DebugCommand<int> get_cmap;
    //public static DebugCommand<List<int>> edit_troop;
    //public static DebugCommand<List<int>> edit_ctroop;
    public static DebugCommand<int> get_troop;
    //public static DebugCommand<int> get_ctroop;
    public static DebugCommand<List<int>> create_troop;
    //public static DebugCommand<int> delete_troop; //Not needed.
    //public static DebugCommand<List<int>> pathfind; //Not needed.
    //Potential commands: Working ways to get and edit data.
    public static DebugCommand debug_mode;
    Vector2 scroll;
    private void Awake()
    {
        showConsole = false;
        debugMode = false;
        controls = new Controls();
        controls.Debug.Enable();
        controls.Debug.DebugConsole.performed += _ => OnConsole();
        controls.Debug.Send.performed += _ => OnEnter();
        controls.Debug.Redo.performed += _ => OnRedo();
        showData = "OFF";

        help = new DebugCommand("help", "Shows list of all commands. You just ran it.", "help", () => { 
            showData = "HELP";  
        });
        /* edit_map = new DebugCommand<List<int>>("edit_map", "Edits a variable of a map tile.", "edit_map <tile> <variable> <value>", (x) => {
            Data.Map[x[0]][x[1]] = x[2];
            TileScript.MapC[x[0]].Add(null);
        }); */
        edit_mapc = new DebugCommand<List<int>>("edit_mapc", "Sends action to the client of a map tile.", "edit_cmap <tile> <value (number)>", (x) => {
            TileScript.MapC[x[0]].Add(x[2].ToString());
            TileScript.MapC[x[0]].Add(null);
        });
        get_map = new DebugCommand<int>("get_map", "Get the data of a map tile.", "get_map <tile>", (x) => {
            showData = string.Join(",", Data.Map[x]);
        });
        get_cmap = new DebugCommand<int>("get_cmap", "Get the client data of a map tile.", "get_cmap <tile>", (x) => {
            showData = string.Join(",", TileScript.MapC[x]);
        });
        /* edit_troop = new DebugCommand<List<int>>("edit_troop", "Edits a variable of a troop.", "edit_troop <troop's tile> <variable> <value>", (x) => {
            Data.Troops[x[0]][x[1]] = x[2];
        });
        edit_ctroop = new DebugCommand<List<int>>("edit_ctroop", "Edits a client variable of a troop.", "edit_cmap <troop's tile> <list> <variable> <value>", (x) => {
            Data.Troopc[x[0]][x[1]][x[2]] = x[3];
        }); */
        get_troop = new DebugCommand<int>("get_troop", "Get the data of a troop.", "get_troop <troop's tile>", (x) => {
            showData = string.Join(",", Data.Troops[x]);
        });
        /* get_ctroop = new DebugCommand<int>("get_ctroop", "Get the client data of a troop.", "get_cmap <troop's tile>", (x) => {
            showData = "";
            for (int i = 0; i < Data.Troopc[x].Count; i++) showData += " / " + string.Join(",", Data.Troopc[x][i]);
        }); */
        create_troop = new DebugCommand<List<int>>("create_troop", "Create a troop.", "create_troop <tile> <country>", (x) => {
            Troop troop = new(Data.Countries[x[1]], Data.Map[x[0]]);
            Data.Map[x[0]].troop = troop;
            Data.Map[x[0]].country = troop.country;
            Data.Troops.Add(troop);
            TroopClient.TroopC.Add(troop, new(troop));
            TileScript.MapC[x[0]].Add(null);
        });
        debug_mode = new DebugCommand("debug_mode", "Turns on debug mode.", "debug_mode", () => {
            debugMode = !debugMode;
        });

        commandList = new List<object> {
            help, edit_mapc, get_map, get_cmap, get_troop, create_troop, debug_mode
        };
    }
    private void OnGUI()
    {
        if (!showConsole) return;
        float offset = 0f;
        if (showData == "HELP") {
            GUI.Box(new Rect(0, offset, Screen.width, 100), "");
            Rect viewport = new(0, 0, Screen.width - 30, 20 * commandList.Count);
            scroll = GUI.BeginScrollView(new Rect(0, offset + 5f, Screen.width, 90), scroll, viewport);
            for (int i = 0; i < commandList.Count; i++) {
                DebugCommandBase command = commandList[i] as DebugCommandBase;
                string label = $"{command.CommandFormat} - {command.CommandDescription}";
                Rect labelRect = new(5, 20 * i, viewport.width - 100, 20);
                GUI.Label(labelRect, label);
            }
            GUI.EndScrollView();
            offset += 100;
        } else if (showData != "OFF") {
            GUI.Box(new Rect(0, offset, Screen.width, 20), "");
            Rect labelRect = new(5, 20 * 0, Screen.width - 50, 20);
            GUI.Label(labelRect, showData);
            offset += 20;
        }
        
        GUI.Box(new Rect(0, offset, Screen.width, 30), "");
        GUI.backgroundColor = Color.clear;
        input = GUI.TextField(new Rect(10f, offset + 5f, Screen.width - 20f, 20f), input);

    }
    private void HandleInput()
    {
        string[] properties = input.Split(' ');
        for (int i = 0; i < commandList.Count; i++) {
            DebugCommandBase commandBase = commandList[i] as DebugCommandBase;
            if (input.Contains(commandBase.CommandID)) {
                if (commandList[i] as DebugCommand != null) {
                    (commandList[i] as DebugCommand).Invoke();
                } else if (commandList[i] as DebugCommand<List<int>> != null) {
                    List<int> x = new() { };
                    for (int j = 1; j < properties.Length; j++ ) x.Add(int.Parse(properties[j]));
                    (commandList[i] as DebugCommand<List<int>>).Invoke(x);
                } else if (commandList[i] as DebugCommand<int> != null) {
                    (commandList[i] as DebugCommand<int>).Invoke(int.Parse(properties[1]));
                }
            }
        }
    }
    private void OnEnter()
    {
        if (!PauseMenu.IsPaused && showConsole) { 
            HandleInput();
            lastCommand = input;
            input = "";
        }
    }
    private void OnConsole()
    {
        if (!PauseMenu.IsPaused) showConsole = !showConsole;
        input = "";
    }
    private void OnRedo()
    {
        if (!PauseMenu.IsPaused) input = lastCommand;
    }
}

public class DebugCommandBase
{
    string _commandId;
    string _commandDescription;
    string _commandFormat;
    public string CommandID { get { return _commandId; } }
    public string CommandDescription { get { return _commandDescription; } }
    public string CommandFormat { get { return _commandFormat; } }
    public DebugCommandBase(string id, string description, string format)
    {
        _commandId = id;
        _commandDescription = description;
        _commandFormat = format;
    }
}

public class DebugCommand : DebugCommandBase
{
    private Action command;
    public DebugCommand(string id, string description, string format, Action command) : base (id, description, format)
    {
        this.command = command;
    }
    public void Invoke()
    {
        command.Invoke();
    }
}

public class DebugCommand<T1> : DebugCommandBase
{
    private Action<T1> command;
    public DebugCommand(string id, string description, string format, Action<T1> command) : base(id, description, format)
    {
        this.command = command;
    }
    public void Invoke(T1 value)
    {
        command.Invoke(value);
    }
}