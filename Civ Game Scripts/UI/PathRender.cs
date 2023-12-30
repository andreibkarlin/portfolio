using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class PathRender : MonoBehaviour
{
    LineRenderer lr;
    private void Awake()
    {
        lr = gameObject.GetComponent<LineRenderer>();
    }
    public void PathRendering(int troop, List<Direction> directions, int colorPreset = 0)
    {
        lr.positionCount = directions.Count + 1;
        int curPos = troop;
        int index = 1;
        lr.SetPosition(0, GenerateV3(curPos));
        for (int direction = 0; direction < directions.Count; direction++) {
            curPos = Pathfinding.Adjacent(curPos, directions[direction]);
            lr.SetPosition(index++, GenerateV3(curPos));
        }
        PathRenderColor(colorPreset);
    }
    public void PathRendering()
    {
        lr.positionCount = 0;
    }
    public void PathRenderColor(int colorPreset)
    {
        if (colorPreset == 0) {
            lr.startColor = Color.cyan;
            lr.endColor = Color.white;
        } else if (colorPreset == 1) {
            lr.startColor = Color.Lerp(Color.red, Color.white, 0.5f);
            lr.endColor = Color.red;
        }
    }
    private Vector3 GenerateV3(int pos)
    {
        int mapSize = 24;
        int padding = 4;
        float height = 0.1f;
        int x = pos % mapSize;
        int z = pos / mapSize;
        return new(padding * x, height , padding * -z);
    }
}
