/**
 * Tests for character-sheet.js - Character Sheet Controller
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import {
    calculateModifier,
    formatModifier,
    calculateHpPercentage,
    getHpColorClass,
    initCharacterSheet,
    updateCharacterSheet,
    updateActiveQuest,
    showCharacterSheet,
    hideCharacterSheet,
    toggleCharacterSheet,
    resetCharacterSheet,
    getCharacterData,
    getQuestData,
    CharacterSheet
} from '../character-sheet.js';

describe('Character Sheet Controller', () => {
    beforeEach(() => {
        // Reset character sheet state
        resetCharacterSheet();
        // Reset document body
        document.body.innerHTML = '';
        // Clear localStorage mock
        localStorage.clear();
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    describe('calculateModifier', () => {
        it('should return +4 for score of 18', () => {
            expect(calculateModifier(18)).toBe(4);
        });

        it('should return +3 for score of 16', () => {
            expect(calculateModifier(16)).toBe(3);
        });

        it('should return +2 for score of 14', () => {
            expect(calculateModifier(14)).toBe(2);
        });

        it('should return +1 for score of 12', () => {
            expect(calculateModifier(12)).toBe(1);
        });

        it('should return 0 for score of 10', () => {
            expect(calculateModifier(10)).toBe(0);
        });

        it('should return 0 for score of 11', () => {
            expect(calculateModifier(11)).toBe(0);
        });

        it('should return -1 for score of 8', () => {
            expect(calculateModifier(8)).toBe(-1);
        });

        it('should return -1 for score of 9', () => {
            expect(calculateModifier(9)).toBe(-1);
        });

        it('should return -2 for score of 6', () => {
            expect(calculateModifier(6)).toBe(-2);
        });

        it('should return -4 for score of 3 (minimum)', () => {
            expect(calculateModifier(3)).toBe(-4);
        });
    });

    describe('formatModifier', () => {
        it('should add + prefix for positive modifiers', () => {
            expect(formatModifier(3)).toBe('+3');
            expect(formatModifier(4)).toBe('+4');
            expect(formatModifier(1)).toBe('+1');
        });

        it('should return "0" for zero modifier', () => {
            expect(formatModifier(0)).toBe('0');
        });

        it('should include - for negative modifiers', () => {
            expect(formatModifier(-1)).toBe('-1');
            expect(formatModifier(-2)).toBe('-2');
            expect(formatModifier(-4)).toBe('-4');
        });
    });

    describe('calculateHpPercentage', () => {
        it('should return 100 for full health', () => {
            expect(calculateHpPercentage(20, 20)).toBe(100);
        });

        it('should return 50 for half health', () => {
            expect(calculateHpPercentage(10, 20)).toBe(50);
        });

        it('should return 0 for no health', () => {
            expect(calculateHpPercentage(0, 20)).toBe(0);
        });

        it('should return 80 for 16/20', () => {
            expect(calculateHpPercentage(16, 20)).toBe(80);
        });

        it('should handle non-20 max HP', () => {
            expect(calculateHpPercentage(15, 30)).toBe(50);
        });

        it('should cap at 100 if current exceeds max', () => {
            expect(calculateHpPercentage(25, 20)).toBe(100);
        });

        it('should return 0 if max HP is 0 or negative', () => {
            expect(calculateHpPercentage(10, 0)).toBe(0);
            expect(calculateHpPercentage(10, -5)).toBe(0);
        });
    });

    describe('getHpColorClass', () => {
        it('should return hp-high for percentage > 50', () => {
            expect(getHpColorClass(100)).toBe('hp-high');
            expect(getHpColorClass(80)).toBe('hp-high');
            expect(getHpColorClass(51)).toBe('hp-high');
        });

        it('should return hp-medium for percentage 26-50', () => {
            expect(getHpColorClass(50)).toBe('hp-medium');
            expect(getHpColorClass(40)).toBe('hp-medium');
            expect(getHpColorClass(26)).toBe('hp-medium');
        });

        it('should return hp-low for percentage <= 25', () => {
            expect(getHpColorClass(25)).toBe('hp-low');
            expect(getHpColorClass(10)).toBe('hp-low');
            expect(getHpColorClass(0)).toBe('hp-low');
        });
    });

    describe('CharacterSheet Controller Object', () => {
        it('should expose all required methods', () => {
            expect(typeof CharacterSheet.init).toBe('function');
            expect(typeof CharacterSheet.show).toBe('function');
            expect(typeof CharacterSheet.hide).toBe('function');
            expect(typeof CharacterSheet.toggle).toBe('function');
            expect(typeof CharacterSheet.update).toBe('function');
            expect(typeof CharacterSheet.updateQuest).toBe('function');
            expect(typeof CharacterSheet.reset).toBe('function');
            expect(typeof CharacterSheet.calculateModifier).toBe('function');
            expect(typeof CharacterSheet.formatModifier).toBe('function');
        });
    });

    describe('DOM Operations', () => {
        beforeEach(() => {
            // Create character sheet DOM structure
            document.body.innerHTML = `
                <div class="character-sheet-panel" id="character-sheet-panel">
                    <div class="character-sheet-header" id="character-sheet-header">
                        <div class="character-sheet-title">
                            <span class="character-sheet-title-text">Character Sheet</span>
                            <div class="character-sheet-summary">
                                <span class="summary-name" id="char-summary-name">--</span>
                                <span id="char-summary-hp">--/--</span>
                            </div>
                        </div>
                        <button class="character-sheet-toggle" id="character-sheet-toggle">
                            <i class="ra ra-arrow-up"></i>
                        </button>
                    </div>
                    <div class="character-sheet-content" id="character-sheet-content">
                        <h3 id="char-name">--</h3>
                        <p id="char-details"><span class="race">--</span> <span class="class">--</span></p>
                        <span id="char-hp-current">--</span>/<span id="char-hp-max">--</span>
                        <div id="char-hp-bar" class="hp-bar-fill" style="width: 100%;"></div>
                        <span id="stat-str">10</span><span id="mod-str">(+0)</span>
                        <span id="stat-dex">10</span><span id="mod-dex">(+0)</span>
                        <span id="stat-con">10</span><span id="mod-con">(+0)</span>
                        <span id="stat-int">10</span><span id="mod-int">(+0)</span>
                        <span id="stat-wis">10</span><span id="mod-wis">(+0)</span>
                        <span id="stat-cha">10</span><span id="mod-cha">(+0)</span>
                        <p id="char-quest-name"></p>
                        <ul id="char-quest-objectives"></ul>
                    </div>
                </div>
            `;

            // Initialize the character sheet
            initCharacterSheet();
        });

        describe('showCharacterSheet', () => {
            it('should add visible class to panel', () => {
                showCharacterSheet();
                const panel = document.getElementById('character-sheet-panel');
                expect(panel.classList.contains('visible')).toBe(true);
            });
        });

        describe('hideCharacterSheet', () => {
            it('should remove visible class from panel', () => {
                showCharacterSheet();
                hideCharacterSheet();
                const panel = document.getElementById('character-sheet-panel');
                expect(panel.classList.contains('visible')).toBe(false);
            });
        });

        describe('toggleCharacterSheet', () => {
            it('should toggle collapsed class on panel', () => {
                const panel = document.getElementById('character-sheet-panel');

                // Get initial state and toggle
                const wasCollapsed = panel.classList.contains('collapsed');
                toggleCharacterSheet();

                // After toggle, should be opposite of initial state
                expect(panel.classList.contains('collapsed')).toBe(!wasCollapsed);

                // Second toggle - should return to initial state
                toggleCharacterSheet();
                expect(panel.classList.contains('collapsed')).toBe(wasCollapsed);
            });

            it('should save collapsed state to localStorage', () => {
                toggleCharacterSheet();
                expect(localStorage.setItem).toHaveBeenCalledWith(
                    'pocket-portals-character-sheet-collapsed',
                    expect.any(String)
                );
            });
        });

        describe('updateCharacterSheet', () => {
            const mockCharacterData = {
                name: 'Thorin',
                race: 'dwarf',
                characterClass: 'fighter',
                level: 1,
                stats: {
                    strength: 16,
                    dexterity: 12,
                    constitution: 14,
                    intelligence: 10,
                    wisdom: 13,
                    charisma: 8
                },
                currentHp: 16,
                maxHp: 20
            };

            it('should update character name', () => {
                updateCharacterSheet(mockCharacterData);
                expect(document.getElementById('char-name').textContent).toBe('Thorin');
            });

            it('should update character summary name', () => {
                updateCharacterSheet(mockCharacterData);
                expect(document.getElementById('char-summary-name').textContent).toBe('Thorin');
            });

            it('should update HP current and max', () => {
                updateCharacterSheet(mockCharacterData);
                expect(document.getElementById('char-hp-current').textContent).toBe('16');
                expect(document.getElementById('char-hp-max').textContent).toBe('20');
            });

            it('should update HP summary', () => {
                updateCharacterSheet(mockCharacterData);
                expect(document.getElementById('char-summary-hp').textContent).toBe('16/20');
            });

            it('should update HP bar width', () => {
                updateCharacterSheet(mockCharacterData);
                const hpBar = document.getElementById('char-hp-bar');
                expect(hpBar.style.width).toBe('80%');
            });

            it('should update stat scores', () => {
                updateCharacterSheet(mockCharacterData);
                expect(document.getElementById('stat-str').textContent).toBe('16');
                expect(document.getElementById('stat-dex').textContent).toBe('12');
                expect(document.getElementById('stat-con').textContent).toBe('14');
                expect(document.getElementById('stat-int').textContent).toBe('10');
                expect(document.getElementById('stat-wis').textContent).toBe('13');
                expect(document.getElementById('stat-cha').textContent).toBe('8');
            });

            it('should update stat modifiers', () => {
                updateCharacterSheet(mockCharacterData);
                expect(document.getElementById('mod-str').textContent).toBe('(+3)');
                expect(document.getElementById('mod-dex').textContent).toBe('(+1)');
                expect(document.getElementById('mod-con').textContent).toBe('(+2)');
                expect(document.getElementById('mod-int').textContent).toBe('(0)');
                expect(document.getElementById('mod-wis').textContent).toBe('(+1)');
                expect(document.getElementById('mod-cha').textContent).toBe('(-1)');
            });

            it('should add negative class to negative modifiers', () => {
                updateCharacterSheet(mockCharacterData);
                expect(document.getElementById('mod-cha').classList.contains('negative')).toBe(true);
                expect(document.getElementById('mod-str').classList.contains('negative')).toBe(false);
            });

            it('should store character data for retrieval', () => {
                updateCharacterSheet(mockCharacterData);
                expect(getCharacterData()).toEqual(mockCharacterData);
            });

            it('should handle null data gracefully', () => {
                expect(() => updateCharacterSheet(null)).not.toThrow();
            });
        });

        describe('updateActiveQuest', () => {
            const mockQuestData = {
                title: 'The Missing Sword',
                objectives: [
                    { id: '1', description: 'Find the blacksmith', isCompleted: true },
                    { id: '2', description: 'Search the ruins', isCompleted: false }
                ]
            };

            it('should update quest name', () => {
                updateActiveQuest(mockQuestData);
                expect(document.getElementById('char-quest-name').textContent).toBe('The Missing Sword');
            });

            it('should update quest objectives', () => {
                updateActiveQuest(mockQuestData);
                const objectives = document.getElementById('char-quest-objectives');
                expect(objectives.children.length).toBe(2);
            });

            it('should mark completed objectives', () => {
                updateActiveQuest(mockQuestData);
                const objectives = document.getElementById('char-quest-objectives');
                expect(objectives.children[0].classList.contains('completed')).toBe(true);
                expect(objectives.children[1].classList.contains('completed')).toBe(false);
            });

            it('should show "No active quest" when data is null', () => {
                updateActiveQuest(null);
                const objectives = document.getElementById('char-quest-objectives');
                expect(objectives.innerHTML).toContain('No active quest');
            });

            it('should store quest data for retrieval', () => {
                updateActiveQuest(mockQuestData);
                expect(getQuestData()).toEqual(mockQuestData);
            });
        });

        describe('resetCharacterSheet', () => {
            it('should clear character data', () => {
                updateCharacterSheet({ name: 'Test', currentHp: 10, maxHp: 20 });
                resetCharacterSheet();
                expect(getCharacterData()).toBeNull();
            });

            it('should clear quest data', () => {
                updateActiveQuest({ title: 'Test Quest', objectives: [] });
                resetCharacterSheet();
                expect(getQuestData()).toBeNull();
            });

            it('should hide the panel', () => {
                showCharacterSheet();
                resetCharacterSheet();
                const panel = document.getElementById('character-sheet-panel');
                expect(panel.classList.contains('visible')).toBe(false);
            });
        });

        describe('initCharacterSheet', () => {
            it('should not throw when panel exists', () => {
                expect(() => initCharacterSheet()).not.toThrow();
            });

            it('should warn when panel is missing', () => {
                document.body.innerHTML = '';
                const warnSpy = vi.spyOn(console, 'warn');
                initCharacterSheet();
                expect(warnSpy).toHaveBeenCalledWith('CharacterSheet: Panel element not found');
            });
        });
    });

    describe('Event Handling', () => {
        beforeEach(() => {
            document.body.innerHTML = `
                <div class="character-sheet-panel" id="character-sheet-panel">
                    <div class="character-sheet-header" id="character-sheet-header" tabindex="0">
                        <button class="character-sheet-toggle" id="character-sheet-toggle"></button>
                    </div>
                    <div class="character-sheet-content" id="character-sheet-content"></div>
                </div>
            `;
            initCharacterSheet();
        });

        it('should toggle on header click', () => {
            const header = document.getElementById('character-sheet-header');
            const panel = document.getElementById('character-sheet-panel');

            // Get initial state
            const wasCollapsed = panel.classList.contains('collapsed');

            header.click();
            // After click, should be opposite of initial state
            expect(panel.classList.contains('collapsed')).toBe(!wasCollapsed);
        });

        it('should toggle on Enter key press', () => {
            const header = document.getElementById('character-sheet-header');
            const panel = document.getElementById('character-sheet-panel');

            // Get initial state
            const wasCollapsed = panel.classList.contains('collapsed');

            const enterEvent = new KeyboardEvent('keydown', { key: 'Enter' });
            header.dispatchEvent(enterEvent);

            // After keypress, should be opposite of initial state
            expect(panel.classList.contains('collapsed')).toBe(!wasCollapsed);
        });

        it('should toggle on Space key press', () => {
            const header = document.getElementById('character-sheet-header');
            const panel = document.getElementById('character-sheet-panel');

            // Get initial state
            const wasCollapsed = panel.classList.contains('collapsed');

            const spaceEvent = new KeyboardEvent('keydown', { key: ' ' });
            header.dispatchEvent(spaceEvent);

            // After keypress, should be opposite of initial state
            expect(panel.classList.contains('collapsed')).toBe(!wasCollapsed);
        });
    });

    describe('Window Exports', () => {
        it('should expose CharacterSheet to window', () => {
            expect(window.CharacterSheet).toBeDefined();
            expect(window.CharacterSheet).toBe(CharacterSheet);
        });

        it('should expose individual functions to window', () => {
            expect(window.initCharacterSheet).toBe(initCharacterSheet);
            expect(window.updateCharacterSheet).toBe(updateCharacterSheet);
            expect(window.updateActiveQuest).toBe(updateActiveQuest);
            expect(window.showCharacterSheet).toBe(showCharacterSheet);
            expect(window.hideCharacterSheet).toBe(hideCharacterSheet);
            expect(window.toggleCharacterSheet).toBe(toggleCharacterSheet);
            expect(window.resetCharacterSheet).toBe(resetCharacterSheet);
            expect(window.calculateModifier).toBe(calculateModifier);
            expect(window.formatModifier).toBe(formatModifier);
        });
    });
});
