using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using TMPro;
//Code for showing and hiding tooltips.
public class Tooltip : MonoBehaviour
{
    [SerializeField] TextMeshProUGUI header;
    [SerializeField] TextMeshProUGUI content;
    [SerializeField] LayoutElement layout;
    [SerializeField] int wrapLimit;
    private static Tooltip tooltip;
    RectTransform rectTransform;
    Controls controls;
    PauseMenu PauseMenu;
    private void Awake() {
        tooltip = this;
        rectTransform = GetComponent<RectTransform>();
        controls = new Controls();
        controls.Game.Enable();
        PauseMenu = FindObjectOfType<PauseMenu>();
    }
    private void Start() {
        Hide();
    }
    public static void Show(string headerText, string contentText)
    {
        tooltip.UpdateThis(headerText, contentText);
        tooltip.gameObject.SetActive(true);
        tooltip.gameObject.transform.position = new Vector3(99999, 99999, 99999); //Move tooltip out of view
    }
    public static void Hide() {
        tooltip.gameObject.SetActive(false);
    }
    private void UpdateThis(string headerText, string contentText)
    {
        int headerLength = header.text.Length;
        int contentLength = content.text.Length;
        layout.enabled = headerLength > wrapLimit || contentLength > wrapLimit;
        header.text = headerText;
        content.text = contentText;
    }
    private void Update()
    {
        gameObject.SetActive(true);
        UpdateThis(gameObject.transform.GetChild(0).GetComponent<TextMeshProUGUI>().text,
        gameObject.transform.GetChild(1).GetComponent<TextMeshProUGUI>().text);
        Vector2 position = controls.Game.MousePosition.ReadValue<Vector2>();
        if (position.magnitude == 0) Hide();
        else {
            transform.position = position;
            float pivotX = position.x / Screen.width;
            float pivotY = position.y / Screen.height;
            if (pivotX > 0.8) pivotX = 1; else pivotX = 0;
            if (pivotY < 0.2) pivotY = 0; else pivotY = 1;
            rectTransform.pivot = new Vector2(pivotX, pivotY);
            if (PauseMenu.IsPaused) Hide();
        }
    }
}
