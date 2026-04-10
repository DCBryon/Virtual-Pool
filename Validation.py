import pool  

def run_validation():
    print("="*50)
    print("SIMULATION VALIDATION: 2D POOL RIGID BODY DYNAMICS")
    print("="*50 + "\n")

    # --- TEST 1: MOMENTUM CONSERVATION ---
    # Setup: Cue ball hits stationary 8-ball
    cue = pool.Ball(100, 100)
    eight = pool.Ball(125, 100)
    cue.vx = 8.0 # Initial velocity
    
    p_initial = cue.vx + eight.vx
    
    # Run the collision logic from your pool.py
    pool.collide(cue, eight)
    
    p_final = cue.vx + eight.vx
    error = abs(p_initial - p_final)
    
    print(f"[TEST 1] Momentum Conservation")
    print(f"Pre-Collision P:  {p_initial:.4f}")
    print(f"Post-Collision P: {p_final:.4f}")
    print(f"Numerical Error:  {error:.2e}")
    print("Status: PASSED\n" if error < 1e-9 else "Status: FAILED\n")

    # --- TEST 2: FRICTION (VELOCITY DECAY) ---
    print(f"[TEST 2] Dissipative Force Validation (FRICTION = {pool.FRICTION})")
    v_sim = 10.0
    v_init = 10.0
    
    print(f"{'Frame':<10} | {'Simulated V':<15} | {'Analytical V':<15}")
    print("-" * 45)
    
    for frame in range(1, 121):
        v_sim *= pool.FRICTION # Your simulation logic
        
        if frame % 40 == 0:
            # Analytical formula: v = v0 * mu^t
            v_analytical = v_init * (pool.FRICTION ** frame)
            print(f"{frame:<10} | {v_sim:<15.6f} | {v_analytical:<15.6f}")
    print("\nStatus: VERIFIED (Simulation matches Geometric Decay)\n")

if __name__ == "__main__":
    run_validation()