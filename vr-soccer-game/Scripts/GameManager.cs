using UnityEngine;
using UnityEngine.UI;
using TMPro;

/// <summary>
/// Main game manager that handles scoring, game state, and UI.
/// Attach this to an empty GameObject in your scene.
/// </summary>
public class GameManager : MonoBehaviour
{
    [Header("Score")]
    public int team1Score = 0;
    public int team2Score = 0;

    [Header("UI References (Optional)")]
    [Tooltip("Text component to display team 1 score")]
    public TextMeshProUGUI team1ScoreText;

    [Tooltip("Text component to display team 2 score")]
    public TextMeshProUGUI team2ScoreText;

    [Tooltip("Text component for announcements (GOAL!, etc)")]
    public TextMeshProUGUI announcementText;

    [Header("World Space UI (for VR)")]
    [Tooltip("3D text or canvas in the world for score display")]
    public TextMeshPro worldScoreDisplay;

    [Header("Game Settings")]
    [Tooltip("Points needed to win (0 = unlimited)")]
    public int pointsToWin = 5;

    [Tooltip("Time limit in seconds (0 = unlimited)")]
    public float timeLimit = 0f;

    [Header("Audio")]
    public AudioClip goalScoreSound;
    public AudioClip gameWinSound;

    // Internal
    private AudioSource audioSource;
    private float gameTimer = 0f;
    private bool gameActive = true;

    // Events
    public delegate void ScoreChangedEvent(int team1, int team2);
    public event ScoreChangedEvent OnScoreChanged;

    public delegate void GameEndedEvent(int winningTeam);
    public event GameEndedEvent OnGameEnded;

    // Singleton for easy access
    public static GameManager Instance { get; private set; }

    void Awake()
    {
        // Simple singleton
        if (Instance == null)
        {
            Instance = this;
        }
        else
        {
            Destroy(gameObject);
            return;
        }

        SetupAudio();
    }

    void Start()
    {
        ResetGame();
    }

    void SetupAudio()
    {
        audioSource = gameObject.AddComponent<AudioSource>();
        audioSource.playOnAwake = false;
    }

    void Update()
    {
        if (!gameActive) return;

        // Update timer if time limit is set
        if (timeLimit > 0)
        {
            gameTimer += Time.deltaTime;

            if (gameTimer >= timeLimit)
            {
                EndGame();
            }
        }
    }

    /// <summary>
    /// Adds a point to the specified team.
    /// </summary>
    public void AddScore(int team)
    {
        if (!gameActive) return;

        if (team == 1)
        {
            team1Score++;
        }
        else if (team == 2)
        {
            team2Score++;
        }

        Debug.Log($"Score: Team 1: {team1Score} - Team 2: {team2Score}");

        // Play sound
        if (audioSource != null && goalScoreSound != null)
        {
            audioSource.PlayOneShot(goalScoreSound);
        }

        // Update UI
        UpdateScoreDisplay();
        ShowAnnouncement("GOAL!", 2f);

        // Notify listeners
        OnScoreChanged?.Invoke(team1Score, team2Score);

        // Check for win condition
        if (pointsToWin > 0 && (team1Score >= pointsToWin || team2Score >= pointsToWin))
        {
            EndGame();
        }
    }

    void UpdateScoreDisplay()
    {
        // Update screen-space UI
        if (team1ScoreText != null)
        {
            team1ScoreText.text = team1Score.ToString();
        }

        if (team2ScoreText != null)
        {
            team2ScoreText.text = team2Score.ToString();
        }

        // Update world-space display (important for VR!)
        if (worldScoreDisplay != null)
        {
            worldScoreDisplay.text = $"{team1Score} - {team2Score}";
        }
    }

    void ShowAnnouncement(string message, float duration)
    {
        if (announcementText != null)
        {
            announcementText.text = message;
            announcementText.gameObject.SetActive(true);
            Invoke(nameof(HideAnnouncement), duration);
        }

        Debug.Log($"Announcement: {message}");
    }

    void HideAnnouncement()
    {
        if (announcementText != null)
        {
            announcementText.gameObject.SetActive(false);
        }
    }

    void EndGame()
    {
        gameActive = false;

        int winner = team1Score > team2Score ? 1 : (team2Score > team1Score ? 2 : 0);

        string message;
        if (winner == 0)
        {
            message = "DRAW!";
        }
        else
        {
            message = $"TEAM {winner} WINS!";
        }

        ShowAnnouncement(message, 5f);

        // Play win sound
        if (audioSource != null && gameWinSound != null)
        {
            audioSource.PlayOneShot(gameWinSound);
        }

        // Notify listeners
        OnGameEnded?.Invoke(winner);

        Debug.Log($"Game ended! {message}");
    }

    /// <summary>
    /// Resets the game to initial state.
    /// </summary>
    public void ResetGame()
    {
        team1Score = 0;
        team2Score = 0;
        gameTimer = 0f;
        gameActive = true;

        UpdateScoreDisplay();
        HideAnnouncement();

        // Reset ball
        SoccerBall ball = FindObjectOfType<SoccerBall>();
        if (ball != null)
        {
            ball.ResetBall();
        }

        Debug.Log("Game reset!");
    }

    /// <summary>
    /// Returns the current game time in seconds.
    /// </summary>
    public float GetGameTime()
    {
        return gameTimer;
    }

    /// <summary>
    /// Returns remaining time if time limit is set, otherwise -1.
    /// </summary>
    public float GetRemainingTime()
    {
        if (timeLimit <= 0) return -1;
        return Mathf.Max(0, timeLimit - gameTimer);
    }

    /// <summary>
    /// Returns true if the game is still active.
    /// </summary>
    public bool IsGameActive()
    {
        return gameActive;
    }
}
