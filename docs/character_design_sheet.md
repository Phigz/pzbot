# Character Design Sheet

Use this template to design new NPC bots for the project. The goal is to create well-rounded, realistic characters that fit within the Project Zomboid universe while providing rich behavioral data for our bot logic.

## 1. Core Identity
*   **Full Name**:
*   **Nickname/Alias**:
*   **Age**:
*   **Gender**:
*   **Occupation (Pre-Apocalypse)**: *See Reference Section below for options*
*   **Origin/Hometown**: (e.g., Muldraugh, West Point, Louisville, or elsewhere)

## 2. In-Game Attributes (Project Zomboid Mechanics)
*   **Profession**: [Start with one from the standard list]
*   **Positive Traits**:
    *   [Trait Name] - [Cost]
    *   [Trait Name] - [Cost]
*   **Negative Traits**:
    *   [Trait Name] - [Bonus]
    *   [Trait Name] - [Bonus]
*   **Resulting Point Balance**: (Should be >= 0)
*   **Key Starting Skills**: (e.g., Carpentry +2, Axe +1)

## 3. Physical Description & Style (Dynamic)
*   **Base Appearance**: (Static traits like height, eye color, tattoos, scars)
*   **Body Weight Tendency**: (e.g., "Struggles to keep weight up", "Easily gains weight", "Maintains athletic build")
*   **Grooming Habits**: (e.g., "Shaves daily despite danger", "Unkempt/Wild", "Practical short cut")
*   **Clothing Strategy**:
    *   *Preferred Aesthetic*: (What they wear when they have a choice, e.g., "Formal wear", "Country casual")
    *   *Survival Compromises*: (How they adapt to scarcity/danger, e.g., "Will wear mismatched padded layers for bites", "Refuses heavy gear to stay fast")

## 4. Personality & Psychology
*   **Archetype**: (e.g., The Reluctant Hero, The Cowardly Hoarder, The Cold Pragmatist)
*   **Core Values**:
    1.  [Value 1]
    2.  [Value 2]
    3.  [Value 3]
*   **Fears & Phobias**: (Beyond standard zombie fear, e.g., Claustrophobia, Hemophobia)
*   **Motivations**: what keeps them going? (Finding family, sheer survival, protecting others?)
*   **Dialogue Style**:
    *   *Tone*: (e.g., Sarcastic, hopeful, silent/grunting)
    *   *Catchphrases/Ticks*:

## 5. Background & Lore
> *Write a brief paragraphs describing where they were when the Knox Event began, who they lost, and how they survived until now.*

**History**:
[Insert text here]

## 6. Behavioral Tendencies (Bot Logic Inputs)
*   **Combat Preference**: [Fight / Flight / Stealth / Negotiate]
*   **Looting Priority**: (e.g., "Prioritizes medical supplies over food", "Obsessed with guns")
*   **Idle Behaviors**: (e.g., "Reads whenever safe", "Organizes inventory continually", "Smokes cigarettes")
*   **Social Stance**: (e.g., "Trusts no one", "Protective of weaker survivors", "Follower")

---

# Reference: Standard Project Zomboid Options

### Professions
*   **Unemployed**: 8 points, no skills.
*   **Fire Officer**: Axe, Fitness, Spirit, Strength.
*   **Police Officer**: Aiming, Nimble, Reloading.
*   **Park Ranger**: Axe, Carpentry, Foraging, Trapping.
*   **Construction Worker**: Short Blunt, Carpentry.
*   **Security Guard**: Lightfooted, Sprinting.
*   **Carpenter**: Carpentry, Short Blunt.
*   **Burglar**: Lightfooted, Nimble, Sneak.
*   **Chef**: Cooking, Maintenance, Short Blade.
*   **Repairman**: Carpentry, Maintenance, Short Blunt.
*   **Farmer**: Farming.
*   **Fisherman**: Fishing, Foraging.
*   **Doctor**: First Aid, Short Blade.
*   **Veteran**: Aiming, Reloading.
*   *And others: Nurse, Lumberjack, Electrician, Engineer, Metalworker, Mechanic.*

### Common Traits
**Positive (Cost Points)**:
*   **Adrenaline Junkie**: Faster when panicked.
*   **Athletic**: Faster running, endurance.
*   **Brave**: Less panic.
*   **Dexterous**: Fast inventory transfer.
*   **Fast Learner**: XP gain +.
*   **Keen Hearing**: Larger perception radius.
*   **Lucky**: Better loot.
*   **Organized**: Larger container capacity.
*   **Stout/Strong**: Knockback, carry weight.

**Negative (Give Points)**:
*   **Clumsy**: More noise.
*   **Conspicuous**: More likely to be spotted.
*   **High Thirst**: Drink more often.
*   **Pacifist**: Less weapon XP.
*   **Smoker**: Needs cigarettes + lighter.
*   **Thin-skinned**: More likely to be scratched/bitten.
*   **Weak Stomach**: Food illness chance.
