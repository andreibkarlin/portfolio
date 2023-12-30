using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

public class TabScript : MonoBehaviour
{
    public string selectedTab;
    int bottomY;
    int topY;
    private void Awake()
    {
        selectedTab = "None";
        bottomY = -27;
        topY = -15;
    }
    public void SelectTab(string tab)
    {
        if (selectedTab == tab) { //Deselect
            GameObject tabObj = gameObject.transform.Find(selectedTab).gameObject;
            Vector3 pos = tabObj.GetComponent<RectTransform>().anchoredPosition;
            pos.y = bottomY;
            tabObj.GetComponent<RectTransform>().anchoredPosition = pos;
            selectedTab = "None";
        } else if (selectedTab != "None") { //Change Selection
            GameObject tabObj = gameObject.transform.Find(selectedTab).gameObject;
            Vector3 pos = tabObj.GetComponent<RectTransform>().anchoredPosition;
            pos.y = bottomY;
            tabObj.GetComponent<RectTransform>().anchoredPosition = pos;
            selectedTab = tab;
            tabObj = gameObject.transform.Find(selectedTab).gameObject;
            pos = tabObj.GetComponent<RectTransform>().anchoredPosition;
            pos.y = topY;
            tabObj.GetComponent<RectTransform>().anchoredPosition = pos;
        } else { //Select
            selectedTab = tab;
            GameObject tabObj = gameObject.transform.Find(selectedTab).gameObject;
            Vector3 pos = tabObj.GetComponent<RectTransform>().anchoredPosition;
            pos.y = topY;
            tabObj.GetComponent<RectTransform>().anchoredPosition = pos;
        }
    }
}
