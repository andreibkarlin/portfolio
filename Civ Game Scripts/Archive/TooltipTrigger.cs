using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.EventSystems;

//This is just a simple trigger script which can be added to the various objects. It references the Tooltip script.
public class TooltipTrigger : MonoBehaviour, IPointerEnterHandler, IPointerExitHandler
{
    public string header;
    [Multiline] public string content;
    public void OnPointerEnter(PointerEventData eventData) {
        Tooltip.Show(header, content);
    }
    public void OnPointerExit(PointerEventData eventdata) {
        Tooltip.Hide();
    }
}
