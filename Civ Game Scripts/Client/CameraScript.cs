using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
//Basic script for camera control. Controls camera movement and zoom, as well as exiting the game.
public class CameraScript : MonoBehaviour
{
    private float panSpeed = 15;
    private float zoomSpeed = 4;
    private float cameraLimit = 96; //24 tiles * tilesize of 4 = 96. Assumes a square grid.
    private float zoomLimitIn = 5;
    private float zoomlimitOut = 90;
    public Controls controls;
    public Ray ray;
    public RaycastHit hit;
    private void Awake()
    {
        controls = new Controls(); //Uses unity's control system.
        controls.Game.Enable();
    }

    private void Update()
    {
        if (DebugConsole.showConsole) controls.Game.Disable(); //If the console is open, don't move the camera if keys are pressed.
        else controls.Game.Enable();
        ray = Camera.main.ScreenPointToRay(controls.Game.MousePosition.ReadValue<Vector2>());
        Vector3 pos = transform.position;
        if (controls.Game.Up.IsPressed()) pos.z += panSpeed * (float)Math.Sqrt(pos.y) * Time.deltaTime;
        if (controls.Game.Left.IsPressed()) pos.x -= panSpeed * (float)Math.Sqrt(pos.y) * Time.deltaTime;
        if (controls.Game.Right.IsPressed()) pos.x += panSpeed * (float)Math.Sqrt(pos.y) * Time.deltaTime;
        if (controls.Game.Down.IsPressed()) pos.z -= panSpeed * (float)Math.Sqrt(pos.y) * Time.deltaTime;
        pos.x = Mathf.Clamp(pos.x, 0, cameraLimit);
        pos.z = Mathf.Clamp(pos.z, -cameraLimit, 0);
        pos.y -= controls.Game.Zoom.ReadValue<float>() * zoomSpeed * Time.deltaTime;
        pos.y = Mathf.Clamp(pos.y, zoomLimitIn, zoomlimitOut);
        transform.position = pos;
    }
}