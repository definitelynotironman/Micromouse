# 3D model

A CAD model of the micromouse I used for the final maze run. It is made from photos of the mouse, so most sizes are close but not measured. The sizes I know exactly come from my code: the wheels are 65 mm across, and the wheel centres are 105 mm apart.

| File | What it is |
|---|---|
| `micromouse.step` | The full model with 44 named parts and their colours. Use this one in Fusion 360. |
| `micromouse.stl` | The same model as one mesh. GitHub shows it in a 3D viewer when you click on it. |
| `build_model.py` | The CadQuery script that builds both files |

## Opening it in Fusion 360

In Fusion 360, go to File, then Open, then Open from my computer, and pick `micromouse.step`. Each part comes in as its own component with its name, for example `tt_motor_left`, `motor_bracket_left` and `main_pcb`.

## What is in the model

| Part | Notes |
|---|---|
| Wheels | 65 mm tyres with a tread pattern, white rims with 8 holes |
| Motors | TT gear motors with the encoder boards on the back |
| Brackets | The yellow 3D printed motor clamps with their posts, rear clips and bolts |
| Boards | The main board with the rear disc, the front sensor board joined to it by a 2 x 16 header, and the STM32 board on top with its chip turned 45 degrees |
| Sensors | The front, left and right ToF sensor boards |
| Other | Battery, rear skid, encoder ribbon cables and connector, headers, solder pads, buttons, nuts and bolts |

## Rebuilding it

```text
pip install cadquery
python build_model.py
```

The script writes `micromouse.step` and `micromouse.glb` to the folder it runs in. Change the numbers at the top of the script to adjust the sizes.
