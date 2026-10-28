# RobotState

`RobotState` holds the numbers the rest of my program reads. It does not drive anything. Keeping them in one place means there is only one true heading and one true position.

```python
class RobotState:
    # heading
    heading            # degrees, added up from the gyro, never wrapped to 0..360
    target_heading     # the heading the controllers are trying to hold
    gyro_bias          # the gyro's zero offset, measured while the mouse is still

    # walls
    left_mm, right_mm  # filtered side distances, or None when there is no wall
    front_mm           # latest front distance
    side_offset        # how far the mouse is from the middle of the passage

    # place in the maze
    cell_x, cell_y     # which cell the mouse is in
    facing             # NORTH, EAST, SOUTH or WEST

    def calibrate_gyro(self):
        average the gyro while the mouse is still and store it as gyro_bias

    def update_heading(self):
        read the gyro, remove the bias, add rate * time step to heading

    def update_wall_estimate(self):
        read the side and front sensors, filter them, work out side_offset
```

I never wrap the heading to 0..360. That way a full spin is just a target 360 degrees away, and the same turn code handles it.
