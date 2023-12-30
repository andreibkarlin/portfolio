using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

//Basic code to create the grid of tiles.
public class GridCreator : MonoBehaviour
{
    //Magic numbers for a 24x24 grid.
    private int rows = 24;
    private int cols = 24;
    private float tileSize = 4;
    private GameObject referenceTile;
    private int tileNum = 0;

    void Start()
    {
        referenceTile = GameObject.Find("Tile");
        GenerateGrid();
    }

    private void GenerateGrid()
    {
        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                GameObject tile = Instantiate(referenceTile, transform); //Creates the tile based on a reference.
                //Sets the tile's position based on calculated x and y values.
                float posX = c * tileSize;
                float posY = r * -tileSize;
                tile.transform.position = new Vector3(Mathf.Round(posX), 0, Mathf.Round(posY));
                tile.name = Convert.ToString(tileNum); //Renames the tile to its number.
                tileNum++;
            }
        }
        Destroy(referenceTile); //The reference tile isn't needed anymore.
    }
}
