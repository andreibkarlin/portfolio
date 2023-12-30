using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using TMPro;

//This script controls the UI, specifically the troop panel.
public class UIHandler : MonoBehaviour
{
    public GameObject canvas;
    Color cyan = Color.HSVToRGB(0.5f, 0.8f, 0.8f);
    Transform panel;
    Transform troopPanel;
    Transform cityPanel;
    Transform infoPanel;
    public void Awake()
    {
        panel = canvas.transform.Find("Selection Panel");
        troopPanel = panel.Find("Troop Panel");
        cityPanel = panel.Find("City Panel");
        infoPanel = canvas.transform.Find("HUD").Find("Info Panel");

    }
    public void UpdateUI()
    {
        int selected = Inputs.GetSelectedTile();
        if (selected >= 0) { //If there is a selection
            SelectionPanel(selected);
        }
        else panel.gameObject.SetActive(false);
        foreach (string resource in GameResources.resourceTypes) {
            infoPanel.Find(resource).Find("Amount").GetComponent<TextMeshProUGUI>().text =
                Data.country.resources.Get(resource).ToString();
            int income = Data.Income(Data.country).Get(resource);
            infoPanel.Find(resource).Find("Income").GetComponent<TextMeshProUGUI>().text = (income >= 0 ? "+" : "") + income.ToString();
            infoPanel.Find(resource).Find("Income").GetComponent<TextMeshProUGUI>().color = income > 0 ? Color.green : income < 0 ? Color.red : Color.white;
        }
    }
    void SelectionPanel(int selected)
    {
        string type = Inputs.GetSelectedType();
        MapTile tile = Data.Map[selected];
        if (type == "Troop") {
            Troop troop = tile.troop;
            //Activate the panel.
            panel.gameObject.SetActive(true);
            troopPanel.gameObject.SetActive(true);
            cityPanel.gameObject.SetActive(false);
            //Update the country GUI
            Transform info = troopPanel.Find("Info");
            Country selectedCountry = troop.country;
            info.Find("Country").GetComponent<TextMeshProUGUI>().text = selectedCountry.name;
            info.Find("Country").GetComponent<TextMeshProUGUI>().color = selectedCountry.color;
            //Update the health GUI and health bar
            int hitpoints = troop.HP;
            info.Find("HP").GetChild(0).GetComponent<TextMeshProUGUI>().text = "HP: " + hitpoints;
            info.Find("Max HP").GetChild(0).GetComponent<TextMeshProUGUI>().text = "" + troop.MaxHP();
            info.Find("Health Bar").GetComponent<Slider>().value = (float)hitpoints / troop.MaxHP();
            string status = troop.Status();
            info.Find("Health Bar").Find("Background").GetComponent<Image>().color =
                (status == "Battle") ? Color.Lerp(Color.magenta, Color.red, 0.5f) : Color.red;
            info.Find("Health Bar").Find("Fill Area").Find("Fill").GetComponent<Image>().color =
                (status == "Garrisoned") ? Color.Lerp(Color.green, Color.cyan, 0.5f) :
                (status == "Alert" || status == "Battle") ? Color.Lerp(Color.green, Color.yellow, 0.5f) :
                Color.green;
            TooltipTrigger tooltip = info.Find("Health Bar").Find("Background").GetComponent<TooltipTrigger>();
            tooltip.header = "Status: " + status;
            switch (status)
            {
                case "Garrisoned": tooltip.content = "Troop is garrisoned in a city. It will not retreat, advance, or mutiny, and it will always regenerate."; break;
                case "Battle": tooltip.content = "Troop fought a battle this turn. It will not regenerate."; break;
                case "Alert": tooltip.content = "Troop fought a battle last turn."; break;
                case "Normal": tooltip.content = "Troop has not fought a battle recently. It is not alert, and it can not retreat."; break;
                default: break;
            }
            //Update other stats, like ATK
            info.Find("ATK").GetChild(0).GetComponent<TextMeshProUGUI>().text = "ATK: " + troop.Attack();
            //Update the movement points GUI
            float movementPoints = troop.MP;
            info.Find("MP").GetChild(0).GetComponent<TextMeshProUGUI>().text = "MP: " + Mathf.Floor(movementPoints) + "/4";
            Transform mpGUI = info.Find("Movement Points");
            for (int i = 0; i < 4; i++) mpGUI.GetChild(i).GetComponent<Image>().color = Color.Lerp(Color.gray, cyan, movementPoints - i);
            //Update the ID tooltip
            info.Find("Type").GetComponent<TooltipTrigger>().content = "ID: " + troop.ID;
        } else if (type == "Building") {
            Building building = tile.building;
            if (building is City city) {
                //Activate the panel
                panel.gameObject.SetActive(true);
                cityPanel.gameObject.SetActive(true);
                troopPanel.gameObject.SetActive(false);
                //Update the country
                Transform info = cityPanel.Find("Info");
                Country selectedCountry = tile.country;
                info.Find("Country").GetComponent<TextMeshProUGUI>().text = selectedCountry.name;
                info.Find("Country").GetComponent<TextMeshProUGUI>().color = selectedCountry.color;
                //Update the stats
                info.Find("POP").GetChild(0).GetComponent<TextMeshProUGUI>().text = "POP: " + city.pops.Count;
                info.Find("HP").GetChild(0).GetComponent<TextMeshProUGUI>().text = "HP: " + city.HP;
                info.Find("ATK").GetChild(0).GetComponent<TextMeshProUGUI>().text = "ATK: " + city.Attack();
                info.Find("Capacity").GetChild(0).GetComponent<TextMeshProUGUI>().text = "Max: " + city.capacity;
                info.Find("Max HP").GetChild(0).GetComponent<TextMeshProUGUI>().text = city.MaxHP().ToString();
                info.Find("Health Bar").GetComponent<Slider>().value = (float)city.HP / city.MaxHP();
                //Update the garrison GUI
                if (tile.HasTroop())
                {
                    info.Find("Garrison").gameObject.SetActive(true);
                    info.Find("Garrison").Find("HP").GetChild(0).GetComponent<TextMeshProUGUI>().text = "+" + tile.troop.HP;
                    info.Find("Garrison").Find("ATK").GetChild(0).GetComponent<TextMeshProUGUI>().text = "+" + tile.troop.Attack();
                }
                else info.Find("Garrison").gameObject.SetActive(false);
                //Update the population GUI
                int pairs = Mathf.CeilToInt((city.capacity - 2f) / 3);
                for (int i = 1; i <= 8; i++)
                {
                    Transform pop = info.Find("Population").Find(i.ToString());
                    //Set it to gray if there is no person.
                    Color color = (i > city.pops.Count) ? Color.gray :
                        //Set it to cyan if there is a breedable person who has a pair. Otherwise, yellow.
                        (i <= pairs * 2 && (i % 2 == 0 || city.pops.Count >= i + 1)) ? new Color(0.14f, 0.7f, 0.7f) : new Color(0.6f, 0.6f, 0.24f);
                    pop.GetComponent<Image>().color = color;
                }
                cityPanel.Find("Buttons").Find("Spawn Troop").GetComponent<Button>().interactable = true; ///Check for population and gold but whatever.
            }
        }
    }
    public void SetSelectMode(string mode)
    {
        canvas.transform.Find("Select Mode").gameObject.SetActive(mode != null);
        canvas.transform.Find("Select Mode").Find("Text").GetComponent<TextMeshProUGUI>().text = mode;
    }
    public void UpdateCountry()
    {
        Country country = Data.country;
        canvas.transform.Find("HUD").Find("Country").GetComponent<TextMeshProUGUI>().text = country.name;
        canvas.transform.Find("HUD").Find("Country").GetComponent<TextMeshProUGUI>().color = country.color;
    }
    public void ButtonInput(string type)
    {
        Inputs.ButtonInput(type);
    }
}
