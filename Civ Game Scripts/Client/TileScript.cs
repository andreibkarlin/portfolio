using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.EventSystems;
//This script processes the client sided behavior of the tiles.
public class TileScript : MonoBehaviour, IPointerEnterHandler, IPointerExitHandler
{
    public static List<string>[] MapC = new List<string>[576];

    [SerializeField] GameObject attached;
    Color color;
    //Color colorChange;
    float[] colorChange;
    int thisTile;
    bool thisTileTooltip;
    bool mouseHover;
    bool update;
    string selection;
    private void Start()
    {
        colorChange = new float[3];
        //colorChange = new Color(Random.Range(-0.1f, 0.1f), Random.Range(-0.1f, 0.1f), Random.Range(-0.1f, 0.1f)); //Randomize the color
        for (int i = 0; i < 3; i++) colorChange[i] = Random.Range(-0.03f, 0.03f);
        attached.GetComponent<SpriteRenderer>().color = UpdateHSV(attached.GetComponent<SpriteRenderer>().color);
        if (gameObject.name != "Tile") thisTile = int.Parse(gameObject.name); //Know its own number.
    }
    private void Update()
    {
        MapTile tile = Data.Map[thisTile];
        UpdateTile(MapC[thisTile]); //Update the tile.
        if (update) { //Color it (or not) based on if it is claimed, show (or not) the troop (if there).
            update = false;
            if (tile.country == null) gameObject.GetComponent<SpriteRenderer>().color = UpdateHSV(Color.white);
            else gameObject.GetComponent<SpriteRenderer>().color = UpdateHSV(tile.country.color);
            gameObject.transform.GetChild(0).gameObject.SetActive(tile.HasTroop());
            gameObject.transform.GetChild(1).gameObject.SetActive(tile.HasBuilding());
            if (tile.isWater) gameObject.GetComponent<SpriteRenderer>().sprite = Resources.Load<Sprite>("Tiles/Water");
            else gameObject.GetComponent<SpriteRenderer>().sprite = Resources.Load<Sprite>("Tiles/Grass");
        }
        if (mouseHover) { //If the mouse is hovering over that, change color and tell that to inputs script.
            color = attached.GetComponent<SpriteRenderer>().color;
            attached.GetComponent<SpriteRenderer>().color = new Color(color.r, color.g, color.b, 0.75f);
            Inputs.SetHover(thisTile);
            if (DebugConsole.debugMode) {
                if (tile.HasTroop()) {
                    Tooltip.Show(tile.troop.ID.ToString(),"");
                    thisTileTooltip = true;
                } else {
                    Tooltip.Show(thisTile.ToString(),"");
                    thisTileTooltip = true;
                }
            } else if (tile.HasCity()) {
                City city = (City)tile.building;
                int hp = city.HP;
                int atk = city.Attack();
                if (tile.HasTroop()) {
                    hp += tile.troop.HP;
                    atk += tile.troop.Attack();
                }
                Tooltip.Show("[" + tile.country.name + "] City",
                    "Pops: " + city.pops.Count + "/" + city.capacity + ", HP: " + hp + ", ATK: " + atk
                    + (tile.HasTroop() ? ", Garrisoned" : ""));
            } else if (tile.HasTroop()) { //If there is a troop, show the tooltip.
                Troop troop = tile.troop;
                string country = troop.country.name;
                Tooltip.Show("["+country+"] Fighter",
                    "HP: " + troop.HP + ", ATK: " + troop.Attack() + ", MP: " + troop.MP.ToString() + "/4");
                thisTileTooltip = true;
            } else {
                thisTileTooltip = false;
                Tooltip.Hide();
            }
        } else if (!mouseHover && !PauseMenu.IsPaused) {
            color = attached.GetComponent<SpriteRenderer>().color;
            attached.GetComponent<SpriteRenderer>().color = new Color(color.r, color.g, color.b, 1f);
            if (thisTileTooltip)
            {
                Tooltip.Hide();
                thisTileTooltip = false;
            }
        }
    }
    public void OnPointerEnter(PointerEventData eventData) {
        mouseHover = true;
    }
    public void OnPointerExit(PointerEventData eventData) {
        mouseHover = false;
        Inputs.SetHover(-1);
    }
    //Updating the tile based on client map data.
    private void UpdateTile(List<string> data)
    {
        if (data.Count > 0) {
            update = true;
            while (data.Contains(null)) data.Remove(null); //If the map client of the tile contains null, that is a sign to update the tile. Remove the null.
            while (data.Count > 0) {
                switch (data[0]) {
                    case "Select": //If the tile is selected, change the selection's color.
                        if (data[1] == "Troop" && Data.Map[thisTile].HasTroop()) {
                            gameObject.transform.Find(data[1]).GetComponent<SpriteRenderer>().color = new Color(0.2f, 0.8f, 0.9f, 1f);
                            selection = "Troop";
                        } else if (data[1] == "Building" && Data.Map[thisTile].HasBuilding()) {
                            gameObject.transform.Find(data[1]).GetComponent<SpriteRenderer>().color = new Color(0.2f, 0.8f, 0.9f, 1f);
                            selection = "Building";
                        }
                        data.RemoveRange(0, 2);
                        break;
                    case "Deselect":
                        if (selection == "Troop")
                            gameObject.transform.Find(selection).GetComponent<SpriteRenderer>().color = Color.black;
                        else if (selection == "Building")
                            gameObject.transform.Find(selection).GetComponent<SpriteRenderer>().color = Color.gray;
                        selection = null;
                        data.RemoveAt(0);
                        break;
                }
            }
        }
    }
    private Color UpdateHSV(Color color) {
        //Color.RGBToHSV(color, out float hue, out float sat, out float val);
        //return Color.HSVToRGB(hue + colorChange[0], sat + colorChange[1], val + colorChange[2]);
        return color;
    }
}
