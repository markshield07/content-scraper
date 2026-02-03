# VR Soccer Game - Complete Setup Guide

This guide walks you through setting up a simple VR soccer game for Quest 3 from scratch.

---

## Part 1: Install Required Software

### Step 1.1: Install Unity Hub
1. Go to https://unity.com/download
2. Download Unity Hub for your operating system
3. Install and open Unity Hub
4. Create a Unity account if you don't have one

### Step 1.2: Install Unity Editor
1. In Unity Hub, click **Installs** → **Install Editor**
2. Choose **Unity 2022.3 LTS** (Long Term Support) - recommended for Quest 3
3. When prompted for modules, make sure to check:
   - ✅ **Android Build Support**
   - ✅ **Android SDK & NDK Tools**
   - ✅ **OpenJDK**
4. Click Install and wait for completion (may take 30+ minutes)

### Step 1.3: Set Up Meta Quest Developer Account
1. Go to https://developer.oculus.com
2. Create or sign in with your Meta account
3. Accept the developer agreement
4. Create an "organization" (can be just your name)

### Step 1.4: Enable Developer Mode on Quest 3
1. On your phone, open the **Meta Quest app**
2. Go to **Menu** → **Devices** → Select your Quest 3
3. Go to **Settings** → **Developer Mode**
4. Toggle **Developer Mode** ON
5. Restart your Quest 3

---

## Part 2: Create Unity Project

### Step 2.1: Create New Project
1. Open Unity Hub
2. Click **New Project**
3. Select **3D Core** template
4. Name it "VRSoccerGame"
5. Choose a location to save
6. Click **Create Project**

### Step 2.2: Install XR Packages
1. In Unity, go to **Window** → **Package Manager**
2. Click the **+** button → **Add package by name**
3. Add these packages one by one:
   ```
   com.unity.xr.interaction.toolkit
   com.unity.xr.oculus
   com.unity.xr.management
   ```
4. For XR Interaction Toolkit, also import the **Starter Assets** when prompted

### Step 2.3: Configure XR Settings
1. Go to **Edit** → **Project Settings** → **XR Plug-in Management**
2. Click **Install XR Plug-in Management** if prompted
3. Under the **Android tab** (robot icon):
   - ✅ Check **Oculus**
4. Under the **PC tab** (monitor icon):
   - ✅ Check **Oculus** (for testing with Link)

### Step 2.4: Configure Android Build Settings
1. Go to **Edit** → **Project Settings** → **Player**
2. Click the **Android tab** (robot icon)
3. Under **Other Settings**:
   - Set **Minimum API Level**: Android 10.0 (API level 29)
   - Set **Scripting Backend**: IL2CPP
   - Set **Target Architectures**: ✅ ARM64 only (uncheck ARMv7)
   - Set **Active Input Handling**: Both (or Input System Package)
4. Under **XR Settings** (if visible):
   - Ensure **Virtual Reality Supported** is enabled

---

## Part 3: Set Up the Scene

### Step 3.1: Create XR Origin
1. Delete the default **Main Camera** from the Hierarchy
2. Right-click in Hierarchy → **XR** → **XR Origin (VR)**
3. This creates your VR player rig with head and hand tracking

### Step 3.2: Create the Soccer Field
1. Right-click in Hierarchy → **3D Object** → **Plane**
2. Rename it to "Field"
3. In Inspector, set Transform:
   - Position: (0, 0, 0)
   - Scale: (5, 1, 3) — this creates a 50m x 30m field
4. Create a green material:
   - Right-click in Project → **Create** → **Material**
   - Name it "GrassMaterial"
   - Set color to green (R:0.2, G:0.6, B:0.2)
   - Drag onto the Field plane

### Step 3.3: Create the Goal
1. Create an empty GameObject: Right-click → **Create Empty**
2. Name it "Goal"
3. Position it at (0, 0, 14) — at the far end of the field

**Create the goal posts:**
1. Right-click on "Goal" → **3D Object** → **Cube**
2. Name it "LeftPost"
3. Set Transform:
   - Position: (-3.66, 1.2, 0)
   - Scale: (0.12, 2.4, 0.12)
4. Duplicate (Ctrl+D), name it "RightPost"
   - Position: (3.66, 1.2, 0)
5. Duplicate again, name it "Crossbar"
   - Position: (0, 2.4, 0)
   - Scale: (7.44, 0.12, 0.12)
6. Create a white material and apply to all posts

### Step 3.4: Create the Soccer Ball
1. Right-click in Hierarchy → **3D Object** → **Sphere**
2. Name it "SoccerBall"
3. Set Transform:
   - Position: (0, 0.5, 5) — in front of the player
   - Scale: (0.22, 0.22, 0.22)
4. Add **Rigidbody** component (Add Component → Rigidbody)
5. Add **Tag**: Click Tag dropdown → **Add Tag** → Create "Ball" → Apply to ball
6. Create a ball material with a soccer pattern or just white

### Step 3.5: Create Goal Detector
1. Right-click on "Goal" → **3D Object** → **Cube**
2. Name it "GoalDetector"
3. Set Transform:
   - Position: (0, 1.2, 0.5) — inside/behind the goal
   - Scale: (7, 2.4, 1)
4. Check **Is Trigger** on the Box Collider
5. Disable or remove the Mesh Renderer (we don't want to see it)

---

## Part 4: Import and Attach Scripts

### Step 4.1: Create Scripts Folder
1. In Project window, right-click → **Create** → **Folder**
2. Name it "Scripts"

### Step 4.2: Copy Scripts
1. Copy all `.cs` files from the `Scripts` folder I created
2. Paste them into your Unity project's Scripts folder
3. Wait for Unity to compile (bottom right progress bar)

### Step 4.3: Create Required Tags
1. Go to **Edit** → **Project Settings** → **Tags and Layers**
2. Under **Tags**, add:
   - "Ball"
   - "Foot"
   - "Goal"

### Step 4.4: Attach Scripts to GameObjects

**On SoccerBall:**
1. Select the SoccerBall in Hierarchy
2. Add Component → Search "SoccerBall" → Add it
3. Make sure the tag is set to "Ball"

**Create Foot Controllers:**
1. Create empty GameObject, name it "FootControllers"
2. Add Component → FootController
3. Set Controller Node to "Left Hand"
4. Duplicate, rename to "RightFootController"
5. Set Controller Node to "Right Hand"

**On GoalDetector:**
1. Select GoalDetector
2. Add Component → GoalDetector
3. Drag the SoccerBall into the Soccer Ball field

**Create GameManager:**
1. Create empty GameObject, name it "GameManager"
2. Add Component → GameManager

**On XR Origin:**
1. Select XR Origin in Hierarchy
2. Add Component → VRPlayerMovement
3. Drag the Main Camera (under XR Origin) to Head Transform field

---

## Part 5: Configure Physics

### Step 5.1: Create Physics Materials
1. Right-click in Project → **Create** → **Physic Material**
2. Name it "BouncyBall"
3. Set properties:
   - Dynamic Friction: 0.4
   - Static Friction: 0.4
   - Bounciness: 0.7
   - Friction Combine: Average
   - Bounce Combine: Maximum
4. Drag onto SoccerBall's Sphere Collider

### Step 5.2: Adjust Ball Rigidbody
1. Select SoccerBall
2. In Rigidbody component:
   - Mass: 0.43
   - Drag: 0.5
   - Angular Drag: 0.5
   - Collision Detection: Continuous Dynamic

---

## Part 6: Test Your Game

### Step 6.1: Test in Editor (Without Headset)
1. Install XR Device Simulator:
   - Window → Package Manager → XR Interaction Toolkit → Samples → Import "XR Device Simulator"
2. Drag the XR Device Simulator prefab into your scene
3. Press Play
4. Use WASD + mouse to simulate VR movement

### Step 6.2: Test with Quest Link
1. Connect Quest 3 to PC via USB-C cable
2. Enable Quest Link on the headset
3. In Unity, press Play
4. Put on headset — you should see the Unity scene!

### Step 6.3: Build to Quest 3
1. Go to **File** → **Build Settings**
2. Click **Android** in platform list
3. Click **Switch Platform** (wait for import)
4. Add your scene: Click **Add Open Scenes**
5. Connect Quest 3 via USB
6. Click **Build and Run**
7. Choose a filename (e.g., "VRSoccer.apk")
8. Wait for build to complete and install on Quest

---

## Part 7: Troubleshooting

### Build fails with "No Android devices found"
- Make sure Developer Mode is ON
- Try a different USB cable (needs data transfer, not just charging)
- Approve the USB debugging prompt on the Quest headset
- Run `adb devices` in terminal to verify connection

### Ball doesn't react to kicks
- Verify the foot objects have the "Foot" tag
- Check that both FootController scripts are active
- Increase kickForceMultiplier in SoccerBall script

### Can't move in VR
- Make sure VRPlayerMovement is on the XR Origin
- Check that headTransform is assigned
- Verify controllers are being detected (check console for debug messages)

### Performance is poor
- Reduce field texture resolution
- Disable shadows: Edit → Project Settings → Quality → Shadows: Disable
- Set Quality Level to "Low" for Android builds

---

## Part 8: Next Steps

Once basic gameplay works, consider adding:

1. **Better visuals**: Import soccer ball texture, grass texture, goal net mesh
2. **Sound effects**: Add kick sounds, goal celebration, crowd ambiance
3. **Scoreboard**: Create a 3D TextMeshPro display in the world
4. **Multiple balls**: Practice with several balls at once
5. **Goalkeeper**: Simple AI that moves to block shots
6. **Multiplayer**: Use Unity Netcode for local multiplayer

---

## Quick Reference: File Structure

```
VRSoccerGame/
├── Assets/
│   ├── Scripts/
│   │   ├── FootController.cs      # Maps controllers to feet
│   │   ├── SoccerBall.cs          # Ball physics and kick detection
│   │   ├── GoalDetector.cs        # Scores goals
│   │   ├── GameManager.cs         # Game state and UI
│   │   ├── VRPlayerMovement.cs    # Locomotion
│   │   └── FieldBoundary.cs       # Resets out-of-bounds ball
│   ├── Materials/
│   │   ├── GrassMaterial.mat
│   │   └── GoalPostMaterial.mat
│   └── Scenes/
│       └── SoccerScene.unity
├── Packages/
└── ProjectSettings/
```

---

## Getting Help

- **Unity XR Documentation**: https://docs.unity3d.com/Manual/XR.html
- **Meta Quest Developer Docs**: https://developer.oculus.com/documentation/unity/
- **Unity Forums**: https://forum.unity.com/
- **YouTube**: Search "Quest 3 Unity tutorial" for video guides

Good luck and have fun building your VR soccer game!
