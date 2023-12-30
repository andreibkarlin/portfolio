using System.Collections;
using System.Collections.Generic;
using UnityEngine;

//This is the main script, that calls other, specialized scripts.
public class Main : MonoBehaviour
{
    int timer;
    [SerializeField] int troopMovementDelay = 3;
    UIHandler UIHandler;
    private void Awake()
    {
        Data.Awake();
        Inputs.ResetVars();
        UIHandler = FindObjectOfType<UIHandler>();
    }
    private void Start()
    {
        Data.GenerateMap();
    }
    private void Update()
    {
        Inputs.HandleInputs();
        UIHandler.UpdateUI();
    }
    private void FixedUpdate()
    {
        timer++;
        if (timer >= troopMovementDelay) {
            TroopClient.HandleTroopMovements();
            timer = 0;
        }
    }
}
