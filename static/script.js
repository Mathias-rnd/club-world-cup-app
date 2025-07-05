// script.js

document.addEventListener('DOMContentLoaded', () => {
    const listEl = document.getElementById('leaderboard-list');
    const detailsPanel = document.getElementById('details-panel');
    const detailsPlayerName = document.getElementById('details-player-name');
    const detailsContent = document.getElementById('details-content');
    const closeButton = document.getElementById('close-button');

    // --- API Functions ---
    async function fetchLeaderboard() {
        const res = await fetch('/api/leaderboard');
        if (!res.ok) throw new Error('Failed to fetch leaderboard');
        return await res.json();
    }

    async function fetchPlayerBets(playerName) {
        const res = await fetch(`/api/bets/${encodeURIComponent(playerName)}`);
        if (!res.ok) throw new Error('Failed to fetch player bets');
        return await res.json();
    }

    function formatScore(score) {
        if (!score || score === "-:-") return score;
        
        // Handle extra time notation
        if (score.includes('aet')) {
            const cleanScore = score.replace('aet', '').trim();
            return `${cleanScore} (AET)`;
        }
        
        // Handle penalty shootout notation
        if (score.includes('pen')) {
            const cleanScore = score.replace('pen', '').trim();
            return `${cleanScore} (PEN)`;
        }
        
        return score;
    }

    async function fetchLiveGame() {
        const container = document.getElementById('live-game-container');
        const content = document.getElementById('live-game-content');
        const header = container.querySelector('.live-game-header');
        try {
            const res = await fetch('/api/live');
            const game = await res.json();
            if (game && game.team1 && game.team2) {
                if (game.score && game.score !== "-:-") {
                    // Game is live
                    container.style.display = 'block';
                    header.innerHTML = `<span class="live-dot"></span> LIVE NOW`;
                    const formattedScore = formatScore(game.score);
                    content.innerHTML = `
                        <span>${game.team1}</span>
                        <span style="font-weight:700; margin: 0 8px;">${formattedScore}</span>
                        <span>${game.team2}</span>
                    `;
                } else {
                    // Game has not started yet
                    container.style.display = 'block';
                    header.innerHTML = `Next game`;
                    // Show the time if available, else just show teams
                    let timeStr = game.time ? `<span style="margin-right:8px;">${game.time}</span>` : '';
                    content.innerHTML = `
                        ${timeStr}
                        <span>${game.team1}</span>
                        <span style="font-weight:700; margin: 0 8px;">vs</span>
                        <span>${game.team2}</span>
                    `;
                }
            } else {
                container.style.display = 'none';
            }
        } catch (e) {
            container.style.display = 'none';
        }
    }

    // --- Rendering Functions ---
    function renderLeaderboard(players) {
        listEl.innerHTML = '';
        if (players.length === 0) {
            listEl.innerHTML = '<div>No data available.</div>';
            return;
        }
        let currentRank = 1;
        let lastScore = null;
        let displayRank = 1;
        players.forEach((player, idx) => {
            if (lastScore !== null && player.score < lastScore) {
                displayRank = currentRank;
            }
            const rowEl = document.createElement('div');
            let rowClass = 'player-row';
            if (displayRank === 1) rowClass += ' top1';
            rowEl.className = rowClass;
            rowEl.innerHTML = `
                <div class="player-rank">${displayRank}</div>
                <div class="player-name" data-player="${player.name}">${player.name}</div>
                <div class="player-score">${player.score} pts</div>
            `;
            listEl.appendChild(rowEl);
            lastScore = player.score;
            currentRank++;
        });
    }

    function renderBetDetails(playerName, bets) {
        detailsPlayerName.textContent = `${playerName}'s Bets`;

        const createList = (betArray) => {
            if (!betArray || betArray.length === 0) return '';
            return `<ul>${betArray.map(bet => `<li class="status-${bet.status}">${bet.team}</li>`).join('')}</ul>`;
        };

        const createPara = (bet, isBar = false) => {
            if (!bet || !bet.team) return '';
            if (isBar && (bet.status === "correct" || bet.status === "incorrect")) {
                return `<div class="status-${bet.status}-bar">${bet.team}</div>`;
            }
            return `<p class="status-${bet.status}">${bet.team}</p>`;
        };

        const createJokerList = (jokers, roundName) => {
            if (!jokers || jokers.length === 0) return '';
            const jokerItems = jokers.map((joker, index) => {
                if (!joker || !joker.team) return '';
                const pointsText = joker.points !== undefined ? ` (${joker.points > 0 ? '+' : ''}${joker.points} pts)` : '';
                return `<li class="status-${joker.status}">Joker ${index + 1}: ${joker.team}${pointsText}</li>`;
            }).filter(item => item !== '');
            
            if (jokerItems.length === 0) return '';
            return `<div class="details-section"><h3>${roundName} Jokers</h3><ul>${jokerItems.join('')}</ul></div>`;
        };

        const sections = {
            '1/8 Final': createList(bets['1/8']),
            '1/4 Final': createList(bets['1/4']),
            '1/2 Final': createList(bets['1/2']),
            'Final': createList(bets['Final']),
            'Winner': createPara(bets.Winner),
            'Best Striker': createPara(bets.BestStriker, true)
        };

        const createSection = (title) => sections[title] ? `<div class="details-section"><h3>${title}</h3>${sections[title]}</div>` : '';

        // Create joker sections
        const jokerSections = [];
        if (bets.Jokers) {
            if (bets.Jokers['1/8']) {
                jokerSections.push(createJokerList(bets.Jokers['1/8'], 'Round of 16'));
            }
            if (bets.Jokers['1/4']) {
                jokerSections.push(createJokerList(bets.Jokers['1/4'], 'Quarter Finals'));
            }
            if (bets.Jokers['1/2']) {
                jokerSections.push(createJokerList(bets.Jokers['1/2'], 'Semi-Finals'));
            }
        }

        const column1 = `<div class="details-column">${createSection('1/8 Final')}</div>`;
        const column2 = `<div class="details-column">${createSection('1/4 Final')}</div>`;
        const column3 = `<div class="details-column">${createSection('1/2 Final')}</div>`;
        const column4 = `<div class="details-column">${createSection('Final')}${createSection('Winner')}${createSection('Best Striker')}${jokerSections.join('')}</div>`;

        detailsContent.innerHTML = column1 + column2 + column3 + column4;
        detailsPanel.classList.add('visible');
        document.querySelector('.container').classList.add('details-open');
    }

    // --- Event Listeners & Main Logic ---
    listEl.addEventListener('click', async (event) => {
        const playerNameEl = event.target.closest('.player-name');
        if (playerNameEl) {
            const playerName = playerNameEl.dataset.player;
            try {
                const bets = await fetchPlayerBets(playerName);
                renderBetDetails(playerName, bets);
            } catch (error) {
                console.error("Failed to show bets:", error);
            }
        }
    });

    closeButton.addEventListener('click', () => {
        detailsPanel.classList.remove('visible');
        document.querySelector('.container').classList.remove('details-open');
    });

    async function updateLeaderboardView() {
        try {
            let players = await fetchLeaderboard();
            players.sort((a, b) => b.score - a.score);
            renderLeaderboard(players);
        } catch (error) {
            console.error('Failed to update leaderboard view:', error);
            listEl.innerHTML = '<div>Could not load data.</div>';
        }
    }

    async function renderTopScorers() {
        const list = document.getElementById('top-scorers-list');
        try {
            const res = await fetch('/api/top_scorers');
            const scorers = await res.json();
            let html = '<ul>';
            let currentRank = 1;
            let lastGoals = null;
            let displayRank = 1;
            scorers.forEach((s, idx) => {
                if (lastGoals !== null && s.Goals < lastGoals) {
                    displayRank = currentRank;
                }
                const goldClass = idx === 0 ? 'gold' : '';
                html += `
                    <li>
                        <span class="data-col data-col-rank ${goldClass}">${displayRank}</span>
                        <span class="data-col data-col-player">
                            ${s.CountryFlagURL ? `<img src="${s.CountryFlagURL}" alt="${s.Country}" class="flag-img">` : ''}
                            <span class="player-name">${s.Player}</span>
                        </span>
                        <span class="data-col data-col-team">
                            ${s.TeamLogoURL ? `<img src="${s.TeamLogoURL}" alt="${s.Team}" class="club-logo-img">` : ''}
                            <span class="club-name">${s.Team}</span>
                        </span>
                        <span class="data-col data-col-goals">${s.Goals}</span>
                    </li>
                `;
                lastGoals = s.Goals;
                currentRank++;
            });
            html += '</ul>';
            list.innerHTML = html;
        } catch (e) {
            list.innerHTML = '<div>Could not load top scorers.</div>';
        }
    }

    // 1. Trigger backend refreshes first and wait for completion
    async function initializePage() {
        try {
            // Trigger all results refresh and top scorers refresh, wait for both
            await Promise.all([
                fetch('/api/refresh_all', { method: 'POST' }),
                fetch('/api/refresh_top_scorers', { method: 'POST' })
            ]);
            // Now fetch and display the fresh data
            await Promise.all([
                fetchLiveGame(),
                updateLeaderboardView(),
                renderTopScorers()
            ]);
        } catch (error) {
            console.error('Error during initialization:', error);
            // Fallback to displaying whatever data is available
            fetchLiveGame();
            updateLeaderboardView();
            renderTopScorers();
        }
    }

    // Initialize the page with fresh data
    initializePage();

    // 3. Keep live game updated every 30 seconds
    setInterval(fetchLiveGame, 30000);
});