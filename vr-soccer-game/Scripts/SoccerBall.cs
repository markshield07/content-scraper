using UnityEngine;

/// <summary>
/// Handles soccer ball physics including kick detection and response.
/// Attach this to a Sphere with a Rigidbody component.
/// </summary>
[RequireComponent(typeof(Rigidbody))]
[RequireComponent(typeof(SphereCollider))]
public class SoccerBall : MonoBehaviour
{
    [Header("Ball Properties")]
    [Tooltip("Mass of the ball in kg (regulation is ~0.43kg)")]
    public float ballMass = 0.43f;

    [Tooltip("How bouncy the ball is (0-1)")]
    [Range(0f, 1f)]
    public float bounciness = 0.7f;

    [Tooltip("Air resistance")]
    public float drag = 0.5f;

    [Tooltip("Rotational air resistance")]
    public float angularDrag = 0.5f;

    [Header("Kick Settings")]
    [Tooltip("Base force multiplier for kicks")]
    public float kickForceMultiplier = 8f;

    [Tooltip("Minimum velocity needed to register as a kick")]
    public float minimumKickVelocity = 0.5f;

    [Tooltip("Maximum force that can be applied")]
    public float maxKickForce = 30f;

    [Tooltip("Upward angle added to kicks (makes ball go up a bit)")]
    [Range(0f, 45f)]
    public float kickUpwardAngle = 15f;

    [Header("Audio (Optional)")]
    public AudioClip kickSound;
    public AudioClip bounceSound;

    [Header("Effects (Optional)")]
    public ParticleSystem kickParticles;

    // Internal references
    private Rigidbody rb;
    private AudioSource audioSource;
    private Vector3 spawnPosition;
    private PhysicMaterial ballPhysicsMaterial;

    // Events for other scripts to listen to
    public delegate void BallKickedEvent(Vector3 force);
    public event BallKickedEvent OnBallKicked;

    void Awake()
    {
        rb = GetComponent<Rigidbody>();
        SetupPhysics();
        SetupAudio();
        spawnPosition = transform.position;
    }

    void SetupPhysics()
    {
        // Configure Rigidbody
        rb.mass = ballMass;
        rb.drag = drag;
        rb.angularDrag = angularDrag;
        rb.collisionDetectionMode = CollisionDetectionMode.ContinuousDynamic;
        rb.interpolation = RigidbodyInterpolation.Interpolate;

        // Create and apply physics material for bounciness
        ballPhysicsMaterial = new PhysicMaterial("BallMaterial");
        ballPhysicsMaterial.bounciness = bounciness;
        ballPhysicsMaterial.frictionCombine = PhysicMaterialCombine.Average;
        ballPhysicsMaterial.bounceCombine = PhysicMaterialCombine.Maximum;
        ballPhysicsMaterial.dynamicFriction = 0.4f;
        ballPhysicsMaterial.staticFriction = 0.4f;

        SphereCollider collider = GetComponent<SphereCollider>();
        collider.material = ballPhysicsMaterial;
    }

    void SetupAudio()
    {
        if (kickSound != null || bounceSound != null)
        {
            audioSource = gameObject.AddComponent<AudioSource>();
            audioSource.playOnAwake = false;
            audioSource.spatialBlend = 1f; // 3D sound
        }
    }

    void OnCollisionEnter(Collision collision)
    {
        // Check if hit by a foot
        if (collision.gameObject.CompareTag("Foot"))
        {
            HandleKick(collision);
        }
        else
        {
            HandleBounce(collision);
        }
    }

    void HandleKick(Collision collision)
    {
        // Try to get FootController for velocity data
        FootController foot = collision.gameObject.GetComponentInParent<FootController>();

        Vector3 footVelocity;
        float kickMultiplier = 1f;

        if (foot != null)
        {
            footVelocity = foot.FootVelocity;
            kickMultiplier = foot.KickPower;
        }
        else
        {
            // Fallback: calculate from collision
            footVelocity = collision.relativeVelocity;
        }

        // Check if kick is strong enough
        float kickSpeed = footVelocity.magnitude;
        if (kickSpeed < minimumKickVelocity)
        {
            return; // Too soft, just let normal physics handle it
        }

        // Calculate kick direction (from foot to ball)
        Vector3 kickDirection = (transform.position - collision.contacts[0].point).normalized;

        // Add some upward angle to make the ball lift
        kickDirection = Quaternion.AngleAxis(-kickUpwardAngle, Vector3.Cross(kickDirection, Vector3.up)) * kickDirection;

        // Calculate force
        float forceMagnitude = kickSpeed * kickForceMultiplier * kickMultiplier;
        forceMagnitude = Mathf.Min(forceMagnitude, maxKickForce);

        Vector3 kickForce = kickDirection * forceMagnitude;

        // Apply the kick
        rb.AddForce(kickForce, ForceMode.Impulse);

        // Add some spin based on where the foot hit the ball
        Vector3 hitOffset = collision.contacts[0].point - transform.position;
        Vector3 spinAxis = Vector3.Cross(kickDirection, hitOffset.normalized);
        rb.AddTorque(spinAxis * forceMagnitude * 0.3f, ForceMode.Impulse);

        // Play effects
        PlayKickEffects(collision.contacts[0].point);

        // Notify listeners
        OnBallKicked?.Invoke(kickForce);

        Debug.Log($"Ball kicked! Force: {forceMagnitude:F1}N, Direction: {kickDirection}");
    }

    void HandleBounce(Collision collision)
    {
        // Play bounce sound if impact is strong enough
        if (collision.relativeVelocity.magnitude > 1f && audioSource != null && bounceSound != null)
        {
            float volume = Mathf.Clamp01(collision.relativeVelocity.magnitude / 10f);
            audioSource.PlayOneShot(bounceSound, volume);
        }
    }

    void PlayKickEffects(Vector3 contactPoint)
    {
        // Play kick sound
        if (audioSource != null && kickSound != null)
        {
            audioSource.PlayOneShot(kickSound);
        }

        // Play particles
        if (kickParticles != null)
        {
            kickParticles.transform.position = contactPoint;
            kickParticles.Play();
        }
    }

    /// <summary>
    /// Resets the ball to its spawn position with zero velocity.
    /// Call this after a goal or when the ball goes out of bounds.
    /// </summary>
    public void ResetBall()
    {
        rb.velocity = Vector3.zero;
        rb.angularVelocity = Vector3.zero;
        transform.position = spawnPosition;
        transform.rotation = Quaternion.identity;
        Debug.Log("Ball reset to spawn position");
    }

    /// <summary>
    /// Resets the ball to a specific position.
    /// </summary>
    public void ResetBall(Vector3 position)
    {
        rb.velocity = Vector3.zero;
        rb.angularVelocity = Vector3.zero;
        transform.position = position;
        transform.rotation = Quaternion.identity;
    }

    /// <summary>
    /// Sets a new spawn position for the ball.
    /// </summary>
    public void SetSpawnPosition(Vector3 position)
    {
        spawnPosition = position;
    }

    // Debug: visualize ball state in editor
    void OnDrawGizmosSelected()
    {
        if (rb != null)
        {
            // Draw velocity vector
            Gizmos.color = Color.blue;
            Gizmos.DrawRay(transform.position, rb.velocity);

            // Draw spawn position
            Gizmos.color = Color.green;
            Gizmos.DrawWireSphere(spawnPosition, 0.15f);
        }
    }
}
