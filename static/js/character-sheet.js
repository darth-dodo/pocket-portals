/**
 * Pocket Portals - Character Sheet Controller
 * Manages the collapsible character sheet panel display
 */

'use strict';

// ===== DOM Element References =====
let characterSheetElements = {
    panel: null,
    header: null,
    toggle: null,
    content: null,
    // Identity
    charName: null,
    charDetails: null,
    summaryName: null,
    summaryHp: null,
    // HP
    hpCurrent: null,
    hpMax: null,
    hpBar: null,
    // Stats
    statStrength: null,
    statDexterity: null,
    statConstitution: null,
    statIntelligence: null,
    statWisdom: null,
    statCharisma: null,
    modStrength: null,
    modDexterity: null,
    modConstitution: null,
    modIntelligence: null,
    modWisdom: null,
    modCharisma: null,
    // Quest
    questName: null,
    questObjectives: null
};

// ===== State =====
let isCollapsed = true; // Default to collapsed on mobile
let characterData = null;
let questData = null;

// LocalStorage key for collapsed state persistence
const COLLAPSED_STORAGE_KEY = 'pocket-portals-character-sheet-collapsed';

/**
 * Calculate ability modifier using D&D 5e formula
 * @param {number} score - Ability score (3-18)
 * @returns {number} Ability modifier (-4 to +4)
 */
export function calculateModifier(score) {
    return Math.floor((score - 10) / 2);
}

/**
 * Format modifier for display with +/- prefix
 * @param {number} mod - Ability modifier
 * @returns {string} Formatted modifier string
 */
export function formatModifier(mod) {
    if (mod === 0) return '0';
    return mod > 0 ? `+${mod}` : `${mod}`;
}

/**
 * Calculate HP bar percentage
 * @param {number} current - Current HP
 * @param {number} max - Maximum HP
 * @returns {number} Percentage (0-100)
 */
export function calculateHpPercentage(current, max) {
    if (max <= 0) return 0;
    return Math.max(0, Math.min(100, (current / max) * 100));
}

/**
 * Get HP bar color class based on percentage
 * @param {number} percentage - HP percentage (0-100)
 * @returns {string} CSS class name
 */
export function getHpColorClass(percentage) {
    if (percentage > 50) return 'hp-high';
    if (percentage > 25) return 'hp-medium';
    return 'hp-low';
}

/**
 * Initialize DOM element references for the character sheet
 */
export function initCharacterSheetElements() {
    characterSheetElements = {
        panel: document.getElementById('character-sheet-panel'),
        header: document.getElementById('character-sheet-header'),
        toggle: document.getElementById('character-sheet-toggle'),
        content: document.getElementById('character-sheet-content'),
        // Identity
        charName: document.getElementById('char-name'),
        charDetails: document.getElementById('char-details'),
        summaryName: document.getElementById('char-summary-name'),
        summaryHp: document.getElementById('char-summary-hp'),
        // HP
        hpCurrent: document.getElementById('char-hp-current'),
        hpMax: document.getElementById('char-hp-max'),
        hpBar: document.getElementById('char-hp-bar'),
        // Stats
        statStrength: document.getElementById('stat-str'),
        statDexterity: document.getElementById('stat-dex'),
        statConstitution: document.getElementById('stat-con'),
        statIntelligence: document.getElementById('stat-int'),
        statWisdom: document.getElementById('stat-wis'),
        statCharisma: document.getElementById('stat-cha'),
        modStrength: document.getElementById('mod-str'),
        modDexterity: document.getElementById('mod-dex'),
        modConstitution: document.getElementById('mod-con'),
        modIntelligence: document.getElementById('mod-int'),
        modWisdom: document.getElementById('mod-wis'),
        modCharisma: document.getElementById('mod-cha'),
        // Quest
        questName: document.getElementById('char-quest-name'),
        questObjectives: document.getElementById('char-quest-objectives')
    };
}

/**
 * Load collapsed state from localStorage
 * @returns {boolean} Whether panel should be collapsed
 */
export function loadCollapsedState() {
    const saved = localStorage.getItem(COLLAPSED_STORAGE_KEY);

    // Default behavior: collapsed on mobile, expanded on desktop
    if (saved === null) {
        return window.innerWidth < 768;
    }

    return saved === 'true';
}

/**
 * Save collapsed state to localStorage
 * @param {boolean} collapsed - Whether panel is collapsed
 */
export function saveCollapsedState(collapsed) {
    localStorage.setItem(COLLAPSED_STORAGE_KEY, collapsed.toString());
}

/**
 * Toggle character sheet collapsed/expanded state
 */
export function toggleCharacterSheet() {
    const { panel } = characterSheetElements;

    if (!panel) return;

    isCollapsed = !isCollapsed;

    if (isCollapsed) {
        panel.classList.add('collapsed');
    } else {
        panel.classList.remove('collapsed');
    }

    // Update ARIA state
    const toggle = characterSheetElements.toggle;
    if (toggle) {
        toggle.setAttribute('aria-expanded', (!isCollapsed).toString());
    }

    // Save preference
    saveCollapsedState(isCollapsed);

    // Trigger haptic feedback
    if (typeof window.hapticFeedback === 'function') {
        window.hapticFeedback('light');
    }
}

/**
 * Show the character sheet panel
 */
export function showCharacterSheet() {
    const { panel } = characterSheetElements;

    if (!panel) return;

    panel.classList.add('visible');

    // Apply saved collapsed state
    isCollapsed = loadCollapsedState();
    if (isCollapsed) {
        panel.classList.add('collapsed');
    } else {
        panel.classList.remove('collapsed');
    }
}

/**
 * Hide the character sheet panel
 */
export function hideCharacterSheet() {
    const { panel } = characterSheetElements;

    if (!panel) return;

    panel.classList.remove('visible');
}

/**
 * Update a single stat display
 * @param {HTMLElement} scoreEl - Score element
 * @param {HTMLElement} modEl - Modifier element
 * @param {number} score - Ability score
 */
function updateStatDisplay(scoreEl, modEl, score) {
    if (scoreEl) {
        scoreEl.textContent = score;
    }

    if (modEl) {
        const mod = calculateModifier(score);
        const formattedMod = formatModifier(mod);
        modEl.textContent = `(${formattedMod})`;

        // Add negative class for styling
        if (mod < 0) {
            modEl.classList.add('negative');
        } else {
            modEl.classList.remove('negative');
        }
    }
}

/**
 * Update the character sheet with new data
 * @param {Object} data - Character data object
 * @param {string} data.name - Character name
 * @param {string} data.race - Character race
 * @param {string} data.characterClass - Character class
 * @param {number} data.level - Character level
 * @param {Object} data.stats - Ability scores object
 * @param {number} data.currentHp - Current HP
 * @param {number} data.maxHp - Maximum HP
 */
export function updateCharacterSheet(data) {
    if (!data) return;

    characterData = data;

    const {
        charName,
        charDetails,
        summaryName,
        summaryHp,
        hpCurrent,
        hpMax,
        hpBar,
        statStrength,
        statDexterity,
        statConstitution,
        statIntelligence,
        statWisdom,
        statCharisma,
        modStrength,
        modDexterity,
        modConstitution,
        modIntelligence,
        modWisdom,
        modCharisma
    } = characterSheetElements;

    // Update identity
    if (charName) {
        charName.textContent = data.name || 'Unknown';
    }

    if (charDetails) {
        const race = data.race ? data.race.charAt(0).toUpperCase() + data.race.slice(1) : 'Unknown';
        const charClass = data.characterClass ? data.characterClass.charAt(0).toUpperCase() + data.characterClass.slice(1) : 'Unknown';
        const level = data.level || 1;
        charDetails.innerHTML = `<span class="race">${race}</span> <span class="class">${charClass}</span> <span class="level">Lv. ${level}</span>`;
    }

    // Update collapsed summary
    if (summaryName) {
        summaryName.textContent = data.name || 'Unknown';
    }

    if (summaryHp && data.currentHp !== undefined && data.maxHp !== undefined) {
        summaryHp.textContent = `${data.currentHp}/${data.maxHp}`;
    }

    // Update HP
    if (hpCurrent && data.currentHp !== undefined) {
        hpCurrent.textContent = data.currentHp;
    }

    if (hpMax && data.maxHp !== undefined) {
        hpMax.textContent = data.maxHp;
    }

    if (hpBar && data.currentHp !== undefined && data.maxHp !== undefined) {
        const percentage = calculateHpPercentage(data.currentHp, data.maxHp);
        hpBar.style.width = `${percentage}%`;

        // Update color class
        hpBar.classList.remove('hp-high', 'hp-medium', 'hp-low');
        hpBar.classList.add(getHpColorClass(percentage));
    }

    // Update stats
    if (data.stats) {
        const stats = data.stats;
        updateStatDisplay(statStrength, modStrength, stats.strength || 10);
        updateStatDisplay(statDexterity, modDexterity, stats.dexterity || 10);
        updateStatDisplay(statConstitution, modConstitution, stats.constitution || 10);
        updateStatDisplay(statIntelligence, modIntelligence, stats.intelligence || 10);
        updateStatDisplay(statWisdom, modWisdom, stats.wisdom || 10);
        updateStatDisplay(statCharisma, modCharisma, stats.charisma || 10);
    }
}

/**
 * Update the active quest display
 * @param {Object|null} data - Quest data object or null if no quest
 * @param {string} data.title - Quest title
 * @param {Array} data.objectives - Quest objectives array
 */
export function updateActiveQuest(data) {
    const { questName, questObjectives } = characterSheetElements;

    if (!data) {
        // No active quest
        if (questName) {
            questName.textContent = '';
        }
        if (questObjectives) {
            questObjectives.innerHTML = '<li class="no-quest">No active quest</li>';
        }
        questData = null;
        return;
    }

    questData = data;

    if (questName) {
        questName.textContent = data.title || 'Unknown Quest';
    }

    if (questObjectives && data.objectives && Array.isArray(data.objectives)) {
        questObjectives.innerHTML = data.objectives.map(objective => {
            const isCompleted = objective.isCompleted || objective.is_completed || false;
            const description = objective.description || objective.text || 'Objective';
            const icon = isCompleted ? 'ra-check' : 'ra-plain-dagger';
            const completedClass = isCompleted ? 'completed' : '';

            return `<li class="quest-objective ${completedClass}">
                <i class="ra ${icon}"></i>
                <span>${description}</span>
            </li>`;
        }).join('');
    } else if (questObjectives) {
        questObjectives.innerHTML = '<li class="no-quest">No objectives</li>';
    }
}

/**
 * Initialize the character sheet controller
 * Sets up DOM references and event listeners
 */
export function initCharacterSheet() {
    // Initialize DOM references
    initCharacterSheetElements();

    const { panel, header, toggle } = characterSheetElements;

    if (!panel) {
        console.warn('CharacterSheet: Panel element not found');
        return;
    }

    // Set initial collapsed state
    isCollapsed = loadCollapsedState();
    if (isCollapsed) {
        panel.classList.add('collapsed');
    }

    // Set up toggle event listeners
    if (header) {
        header.addEventListener('click', toggleCharacterSheet);
        header.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                toggleCharacterSheet();
            }
        });
    }

    if (toggle) {
        toggle.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent double-toggle from header click
            toggleCharacterSheet();
        });
        toggle.setAttribute('aria-expanded', (!isCollapsed).toString());
    }

    console.log('CharacterSheet controller initialized');
}

/**
 * Reset character sheet state (for testing or new game)
 */
export function resetCharacterSheet() {
    characterData = null;
    questData = null;
    hideCharacterSheet();
}

/**
 * Get current character data (for testing)
 * @returns {Object|null} Current character data
 */
export function getCharacterData() {
    return characterData;
}

/**
 * Get current quest data (for testing)
 * @returns {Object|null} Current quest data
 */
export function getQuestData() {
    return questData;
}

// ===== CharacterSheet Controller Object =====
export const CharacterSheet = {
    init: initCharacterSheet,
    show: showCharacterSheet,
    hide: hideCharacterSheet,
    toggle: toggleCharacterSheet,
    update: updateCharacterSheet,
    updateQuest: updateActiveQuest,
    reset: resetCharacterSheet,
    calculateModifier,
    formatModifier,
    getCharacterData,
    getQuestData
};

// Browser compatibility: expose to window for script tag usage
if (typeof window !== 'undefined') {
    window.CharacterSheet = CharacterSheet;
    window.initCharacterSheet = initCharacterSheet;
    window.updateCharacterSheet = updateCharacterSheet;
    window.updateActiveQuest = updateActiveQuest;
    window.showCharacterSheet = showCharacterSheet;
    window.hideCharacterSheet = hideCharacterSheet;
    window.toggleCharacterSheet = toggleCharacterSheet;
    window.resetCharacterSheet = resetCharacterSheet;
    window.calculateModifier = calculateModifier;
    window.formatModifier = formatModifier;
}
