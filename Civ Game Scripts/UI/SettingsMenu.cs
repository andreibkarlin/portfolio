using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

public class SettingsMenu : MonoBehaviour
{
    //[SerializeField] UnityEngine.Audio.AudioMixer Mixer;
    [SerializeField] Slider vSlider;
    [SerializeField] Toggle fScreen;
    [SerializeField] Toggle sPF;
    [SerializeField] Toggle sC;
    public static float GameVolume;
    public static bool inFS = true;
    public static bool straightPathfinding;
    public static bool switchCountries;
    private void Start()
    {
        vSlider.value = GameVolume;
        fScreen.isOn = inFS;
        sPF.isOn = straightPathfinding;
    }
    public void VolumeSlider()
    {
        //Mixer.SetFloat("Volume", volume);
        GameVolume = vSlider.value;
    }
    public void FullScreenMode()
    {
        inFS = Screen.fullScreen = fScreen.isOn;
    }
    public void StraightPathfinding()
    {
        straightPathfinding = sPF.isOn;
    }
    public void SwitchCountries()
    {
        switchCountries = sC.isOn;
    }
}
