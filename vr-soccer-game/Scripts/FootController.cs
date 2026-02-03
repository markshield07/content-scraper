using UnityEngine;
using UnityEngine.XR;
using System.Collections.Generic;

/// <summary>
/// Maps a VR controller to act as a virtual foot.
/// Attach this to an empty GameObject in your scene.
/// You'll need two instances - one for left foot, one for right foot.
/// </summary>
public class FootController : MonoBehaviour
{
    [Header("Controller Settings")]
    [Tooltip("Which controller controls this foot")]
    public XRNode controllerNode = XRNode.LeftHand;

    [Header("Foot Positioning")]
    [Tooltip("Offset from controller position to foot position")]
    public Vector3 positionOffset = new Vector3(0f, -0.7f, 0.2f);

    [Tooltip("Rotation offset for the foot")]
    public Vector3 rotationOffset = new Vector3(90f, 0f, 0f);

    [Header("Foot Appearance")]
    [Tooltip("Size of the foot collider")]
    public Vector3 footSize = new Vector3(0.1f, 0.15f, 0.28f);

    [Tooltip("Color of the foot (for visibility during development)")]
    public Color footColor = Color.white;

    [Header("Physics")]
    [Tooltip("How much the foot affects the ball")]
    public float kickPowerMultiplier = 1.5f;

    // Internal references
    private GameObject footObject;
    private Rigidbody footRigidbody;
    private InputDevice controller;
    private Vector3 previousPosition;
    private Vector3 currentVelocity;

    // Public property for other scripts to read foot velocity
    public Vector3 FootVelocity => currentVelocity;
    public float KickPower => kickPowerMultiplier;

    void Start()
    {
        CreateFootObject();
        FindController();
    }

    void CreateFootObject()
    {
        // Create the foot GameObject
        footObject = GameObject.CreatePrimitive(PrimitiveType.Cube);
        footObject.name = controllerNode == XRNode.LeftHand ? "LeftFoot" : "RightFoot";
        footObject.tag = "Foot";
        footObject.transform.localScale = footSize;

        // Set up the material/color
        Renderer renderer = footObject.GetComponent<Renderer>();
        renderer.material = new Material(Shader.Find("Standard"));
        renderer.material.color = footColor;

        // Add Rigidbody for physics interactions
        footRigidbody = footObject.AddComponent<Rigidbody>();
        footRigidbody.isKinematic = true; // We control position manually
        footRigidbody.useGravity = false;
        footRigidbody.collisionDetectionMode = CollisionDetectionMode.ContinuousDynamic;

        // Store initial position
        previousPosition = footObject.transform.position;
    }

    void FindController()
    {
        List<InputDevice> devices = new List<InputDevice>();
        InputDevices.GetDevicesAtXRNode(controllerNode, devices);

        if (devices.Count > 0)
        {
            controller = devices[0];
            Debug.Log($"Found controller for {controllerNode}: {controller.name}");
        }
    }

    void Update()
    {
        // Try to find controller if not connected
        if (!controller.isValid)
        {
            FindController();
            return;
        }

        UpdateFootPosition();
        CalculateVelocity();
    }

    void UpdateFootPosition()
    {
        // Get controller position and rotation
        if (controller.TryGetFeatureValue(CommonUsages.devicePosition, out Vector3 controllerPos) &&
            controller.TryGetFeatureValue(CommonUsages.deviceRotation, out Quaternion controllerRot))
        {
            // Calculate foot position with offset
            Vector3 worldOffset = controllerRot * positionOffset;
            Vector3 targetPosition = controllerPos + worldOffset;

            // Calculate foot rotation with offset
            Quaternion targetRotation = controllerRot * Quaternion.Euler(rotationOffset);

            // Apply to foot object
            footObject.transform.position = targetPosition;
            footObject.transform.rotation = targetRotation;
        }
    }

    void CalculateVelocity()
    {
        // Calculate velocity for kick force calculations
        currentVelocity = (footObject.transform.position - previousPosition) / Time.deltaTime;
        previousPosition = footObject.transform.position;
    }

    void OnDestroy()
    {
        if (footObject != null)
        {
            Destroy(footObject);
        }
    }

    // Debug visualization in editor
    void OnDrawGizmos()
    {
        if (footObject != null)
        {
            Gizmos.color = Color.yellow;
            Gizmos.DrawWireCube(footObject.transform.position, footSize);

            // Draw velocity vector
            Gizmos.color = Color.red;
            Gizmos.DrawRay(footObject.transform.position, currentVelocity * 0.5f);
        }
    }
}
