using UnityEngine;
using UnityEngine.XR;
using System.Collections.Generic;

/// <summary>
/// Simple VR locomotion using thumbstick movement.
/// Attach this to your XR Origin/XR Rig GameObject.
/// Left stick = move, Right stick = turn.
/// </summary>
public class VRPlayerMovement : MonoBehaviour
{
    [Header("Movement Settings")]
    [Tooltip("Movement speed in meters per second")]
    public float moveSpeed = 3f;

    [Tooltip("Sprint speed multiplier when holding grip")]
    public float sprintMultiplier = 1.8f;

    [Tooltip("How quickly movement accelerates")]
    public float acceleration = 10f;

    [Header("Rotation Settings")]
    [Tooltip("Use snap turning (true) or smooth turning (false)")]
    public bool useSnapTurn = true;

    [Tooltip("Degrees to rotate per snap turn")]
    public float snapTurnAngle = 45f;

    [Tooltip("Smooth turn speed in degrees per second")]
    public float smoothTurnSpeed = 90f;

    [Tooltip("Deadzone for thumbstick input")]
    [Range(0f, 0.5f)]
    public float thumbstickDeadzone = 0.2f;

    [Header("References")]
    [Tooltip("The camera/head transform (auto-finds if not set)")]
    public Transform headTransform;

    // Internal
    private InputDevice leftController;
    private InputDevice rightController;
    private CharacterController characterController;
    private Vector3 currentVelocity;
    private bool canSnapTurn = true;
    private float snapTurnCooldown = 0.3f;
    private float lastSnapTime;

    void Start()
    {
        // Find or add CharacterController
        characterController = GetComponent<CharacterController>();
        if (characterController == null)
        {
            characterController = gameObject.AddComponent<CharacterController>();
            characterController.height = 1.8f;
            characterController.radius = 0.15f;
            characterController.center = new Vector3(0, 0.9f, 0);
        }

        // Find head/camera
        if (headTransform == null)
        {
            Camera mainCam = GetComponentInChildren<Camera>();
            if (mainCam != null)
            {
                headTransform = mainCam.transform;
            }
        }

        FindControllers();
    }

    void FindControllers()
    {
        List<InputDevice> devices = new List<InputDevice>();

        // Find left controller
        InputDevices.GetDevicesAtXRNode(XRNode.LeftHand, devices);
        if (devices.Count > 0)
        {
            leftController = devices[0];
        }

        // Find right controller
        devices.Clear();
        InputDevices.GetDevicesAtXRNode(XRNode.RightHand, devices);
        if (devices.Count > 0)
        {
            rightController = devices[0];
        }
    }

    void Update()
    {
        // Try to find controllers if disconnected
        if (!leftController.isValid || !rightController.isValid)
        {
            FindControllers();
        }

        HandleMovement();
        HandleRotation();
        ApplyGravity();
    }

    void HandleMovement()
    {
        // Get left thumbstick input
        Vector2 moveInput = Vector2.zero;
        if (leftController.isValid)
        {
            leftController.TryGetFeatureValue(CommonUsages.primary2DAxis, out moveInput);
        }

        // Apply deadzone
        if (moveInput.magnitude < thumbstickDeadzone)
        {
            moveInput = Vector2.zero;
        }

        // Check for sprint (grip button)
        float currentSpeed = moveSpeed;
        if (leftController.TryGetFeatureValue(CommonUsages.gripButton, out bool gripPressed) && gripPressed)
        {
            currentSpeed *= sprintMultiplier;
        }

        // Calculate move direction relative to head facing
        Vector3 forward = headTransform != null ? headTransform.forward : transform.forward;
        Vector3 right = headTransform != null ? headTransform.right : transform.right;

        // Flatten to horizontal plane
        forward.y = 0;
        forward.Normalize();
        right.y = 0;
        right.Normalize();

        // Calculate target velocity
        Vector3 targetVelocity = (forward * moveInput.y + right * moveInput.x) * currentSpeed;

        // Smooth acceleration
        currentVelocity = Vector3.Lerp(currentVelocity, targetVelocity, acceleration * Time.deltaTime);

        // Apply movement
        if (characterController != null && currentVelocity.magnitude > 0.01f)
        {
            characterController.Move(currentVelocity * Time.deltaTime);
        }
    }

    void HandleRotation()
    {
        // Get right thumbstick input
        Vector2 turnInput = Vector2.zero;
        if (rightController.isValid)
        {
            rightController.TryGetFeatureValue(CommonUsages.primary2DAxis, out turnInput);
        }

        // Apply deadzone
        if (Mathf.Abs(turnInput.x) < thumbstickDeadzone)
        {
            turnInput.x = 0;
        }

        if (useSnapTurn)
        {
            HandleSnapTurn(turnInput.x);
        }
        else
        {
            HandleSmoothTurn(turnInput.x);
        }
    }

    void HandleSnapTurn(float input)
    {
        // Check cooldown
        if (Time.time - lastSnapTime < snapTurnCooldown)
        {
            return;
        }

        // Snap turn when thumbstick pushed past threshold
        if (Mathf.Abs(input) > 0.7f && canSnapTurn)
        {
            float turnDirection = Mathf.Sign(input);
            transform.RotateAround(headTransform.position, Vector3.up, snapTurnAngle * turnDirection);
            canSnapTurn = false;
            lastSnapTime = Time.time;
        }

        // Reset when thumbstick returns to center
        if (Mathf.Abs(input) < 0.3f)
        {
            canSnapTurn = true;
        }
    }

    void HandleSmoothTurn(float input)
    {
        if (Mathf.Abs(input) > thumbstickDeadzone)
        {
            float turnAmount = input * smoothTurnSpeed * Time.deltaTime;
            transform.RotateAround(headTransform.position, Vector3.up, turnAmount);
        }
    }

    void ApplyGravity()
    {
        // Simple gravity
        if (characterController != null && !characterController.isGrounded)
        {
            characterController.Move(Vector3.down * 9.81f * Time.deltaTime);
        }
    }

    // Debug info
    void OnGUI()
    {
        if (Debug.isDebugBuild)
        {
            GUILayout.BeginArea(new Rect(10, 10, 300, 100));
            GUILayout.Label($"Speed: {currentVelocity.magnitude:F1} m/s");
            GUILayout.Label($"Grounded: {characterController?.isGrounded}");
            GUILayout.EndArea();
        }
    }
}
