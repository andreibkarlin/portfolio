using System.Collections;
using System.Collections.Generic;
using UnityEngine;
//Script to control the pause menu.
public class PauseMenu : MonoBehaviour
{
    public static bool IsPaused;
    [SerializeField] GameObject PauseUI;
    GameObject settingsMenu;
    GameObject pausePanel;
    Controls controls;
    bool settings;
    //[SerializeField] GameObject Camera;
    private void Awake()
    {
        IsPaused = false;
        controls = new Controls();
        controls.Menus.Enable();
        settingsMenu = PauseUI.transform.Find("Settings Panel").gameObject;
        pausePanel = PauseUI.transform.Find("Pause Panel").gameObject;
    }
    private void Update()
    {
        if (controls.Menus.Pause.triggered) Pause();
    }
    public void Pause()
    {
        if (IsPaused) Resume();
        else {
            PauseUI.SetActive(true);
            Time.timeScale = 0f;
            IsPaused = true;
            //Camera.GetComponent<AudioSource>().Pause();
            DebugConsole.showConsole = false;
        }
    }
    public void Resume()
    {
        if (settings) Settings();
        else {
            PauseUI.SetActive(false);
            Time.timeScale = 1f;
            IsPaused = false;
            //Camera.GetComponent<AudioSource>().Play();
        }
    }
    public void ToMenu()
    {
        Time.timeScale = 1f;
        UnityEngine.SceneManagement.SceneManager.LoadScene("MainMenu");
    }
    public void Settings()
    {
        settingsMenu.SetActive(!settingsMenu.activeInHierarchy);
        pausePanel.SetActive(!pausePanel.activeInHierarchy);
        settings = !settings;
    }
}
