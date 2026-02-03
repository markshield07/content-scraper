using UnityEngine;

/// <summary>
/// Detects when the ball enters the goal and triggers scoring.
/// Attach this to an empty GameObject with a Box Collider (set as Trigger)
/// positioned inside/behind the goal.
/// </summary>
[RequireComponent(typeof(Collider))]
public class GoalDetector : MonoBehaviour
{
    [Header("References")]
    [Tooltip("Reference to the GameManager (auto-finds if not set)")]
    public GameManager gameManager;

    [Tooltip("Reference to the soccer ball (auto-finds if not set)")]
    public SoccerBall soccerBall;

    [Header("Goal Settings")]
    [Tooltip("Which team scores when ball enters this goal")]
    public int teamThatScores = 1;

    [Tooltip("Time to wait before resetting ball after goal")]
    public float resetDelay = 2f;

    [Header("Effects")]
    public AudioClip goalSound;
    public ParticleSystem goalParticles;
    public GameObject goalCelebrationPrefab;

    // Internal
    private AudioSource audioSource;
    private bool goalScored = false;

    // Events
    public delegate void GoalScoredEvent(int team);
    public event GoalScoredEvent OnGoalScored;

    void Start()
    {
        // Ensure collider is set as trigger
        Collider col = GetComponent<Collider>();
        col.isTrigger = true;

        // Auto-find references if not set
        if (gameManager == null)
        {
            gameManager = FindObjectOfType<GameManager>();
        }

        if (soccerBall == null)
        {
            soccerBall = FindObjectOfType<SoccerBall>();
        }

        // Setup audio
        if (goalSound != null)
        {
            audioSource = gameObject.AddComponent<AudioSource>();
            audioSource.playOnAwake = false;
            audioSource.spatialBlend = 0.5f;
        }
    }

    void OnTriggerEnter(Collider other)
    {
        // Check if it's the ball
        if (!other.CompareTag("Ball"))
        {
            return;
        }

        // Prevent multiple goal triggers
        if (goalScored)
        {
            return;
        }

        goalScored = true;

        Debug.Log($"GOAL! Team {teamThatScores} scores!");

        // Notify GameManager
        if (gameManager != null)
        {
            gameManager.AddScore(teamThatScores);
        }

        // Play effects
        PlayGoalEffects(other.transform.position);

        // Notify listeners
        OnGoalScored?.Invoke(teamThatScores);

        // Reset ball after delay
        Invoke(nameof(ResetAfterGoal), resetDelay);
    }

    void PlayGoalEffects(Vector3 ballPosition)
    {
        // Play sound
        if (audioSource != null && goalSound != null)
        {
            audioSource.PlayOneShot(goalSound);
        }

        // Play particles
        if (goalParticles != null)
        {
            goalParticles.transform.position = ballPosition;
            goalParticles.Play();
        }

        // Spawn celebration effect
        if (goalCelebrationPrefab != null)
        {
            GameObject celebration = Instantiate(goalCelebrationPrefab, ballPosition, Quaternion.identity);
            Destroy(celebration, 3f); // Clean up after 3 seconds
        }
    }

    void ResetAfterGoal()
    {
        // Reset the ball
        if (soccerBall != null)
        {
            soccerBall.ResetBall();
        }

        // Allow goals to be scored again
        goalScored = false;
    }

    // Visualize goal zone in editor
    void OnDrawGizmos()
    {
        Collider col = GetComponent<Collider>();
        if (col != null)
        {
            Gizmos.color = new Color(0f, 1f, 0f, 0.3f);

            if (col is BoxCollider box)
            {
                Gizmos.matrix = transform.localToWorldMatrix;
                Gizmos.DrawCube(box.center, box.size);
                Gizmos.DrawWireCube(box.center, box.size);
            }
        }
    }
}
