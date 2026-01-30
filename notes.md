# notes

base direction (down, downright, right, rightup, up)
gun (unarmed, pistol, smg, shotgun, rifle)
leg animation (idle, walk, crouch)
torso animation (idle, walk)

head direction (co-aligned)


walking / running: set legs and torso animation
gun animations: use idle legs, or crouch


unarmed:
    walk: legs and unarmed torso walking
    run: legs and unarmed torso running
pistol: (use both legs idle and legs crouching)
    shoot
    rack
    reload
smg: (use both legs idle and legs crouching)
    shoot
    rack
    reload
    run


. jack torso too high- should extend lower to cover.
. scientist, security leg sprites are unfinished at their tops.
 . fix jack smg
. fix jack rifle
. fix jack shotgun.


test pixel scaler in build


# recolor

1. determine a set of standardized skin tones
2. mass apply the recoloring
    save output into its own directory
    process all skins simultaneously
3. import into DJ2020