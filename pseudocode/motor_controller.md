# MotorController

`MotorController` owns the motors. It knows how to do one move at a time and report what it saw. It knows nothing about the maze.

```python
class MotorController:
    state              # the RobotState it reads and updates

    def drive_straight(self, cells, top_speed):
        until the mouse reaches the target or sees a wall ahead:
            hold the heading with a PID controller
            nudge the heading to stay in the middle of the passage
            slow down near the end
            wait for the next control tick
        stop, and report how far it went and why it stopped

    def turn_to_heading(self, target):
        spin towards the target
        cut the power a little early so the mouse coasts in
        once it is still, check the error and try again if it is too far off

    def scan_walls(self):
        sit still for a moment, take a few readings, return left, front and right

    def wait_one_tick(self):
        wait one control period, then run the background jobs that read the sensors
```

The controller also learns a few things while it runs, like how much stronger one motor is than the other. The design behind it is in the main README under [My chosen control system design](../README.md#my-chosen-control-system-design).
