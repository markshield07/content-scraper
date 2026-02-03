using UnityEngine;

/// <summary>
/// Resets the ball when it goes out of bounds.
/// Attach this to a large trigger collider surrounding (but outside) the play area.
/// </summary>
[RequireComponent(typeof(Collider))]
public class FieldBoundary : MonoBehaviour
{
    [Header("References")]
    public SoccerBall soccerBall;

    [Header("Settings")]
    [Tooltip("Position to reset ball to when out of bounds")]
    public Transform resetPosition;

    [Tooltip("Delay before resetting ball")]
    public float resetDelay = 1f;

    [Header("Audio")]
    public AudioClip outOfBoundsSound;

    private AudioSource audioSource;
    private bool isResetting = false;

    void Start()
    {
        // Ensure collider is trigger
        GetComponent<Collider>().isTrigger = true;

        // Auto-find ball
        if (soccerBall == null)
        {
            soccerBall = FindObjectOfType<SoccerBall>();
        }

        // Setup audio
        if (outOfBoundsSound != null)
        {
            audioSource = gameObject.AddComponent<AudioSource>();
            audioSource.playOnAwake = false;
        }
    }

    void OnTriggerExit(Collider other)
    {
        // Ball left the boundary area (went out of bounds)
        if (other.CompareTag("Ball") && !isResetting)
        {
            Debug.Log("Ball out of bounds!");
            isResetting = true;

            // Play sound
            if (audioSource != null && outOfBoundsSound != null)
            {
                audioSource.PlayOneShot(outOfBoundsSound);
            }

            Invoke(nameof(ResetBall), resetDelay);
        }
    }

    void ResetBall()
    {
        if (soccerBall != null)
        {
            if (resetPosition != null)
            {
                soccerBall.ResetBall(resetPosition.position);
            }
            else
            {
                soccerBall.ResetBall();
            }
        }

        isResetting = false;
    }

    // Visualize boundary in editor
    void OnDrawGizmos()
    {
        Collider col = GetComponent<Collider>();
        if (col is BoxCollider box)
        {
            Gizmos.color = new Color(1f, 0f, 0f, 0.2f);
            Gizmos.matrix = transform.localToWorldMatrix;
            Gizmos.DrawWireCube(box.center, box.size);
        }
    }
}
