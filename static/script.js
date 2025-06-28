// script.js

document.addEventListener('DOMContentLoaded', () => {
    const listEl = document.getElementById('leaderboard-list');
    const refreshButton = document.getElementById('refresh-button');
    const loader = document.getElementById('loader');
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

    async function triggerRefresh() {
        refreshButton.disabled = true;
        loader.style.display = 'block';

        try {
            const res = await fetch('/api/refresh', { method: 'POST' });
            const data = await res.json();
            if (!data.success) {
                throw new Error(data.message || 'Refresh failed on the server.');
            }
            console.log("Live data refresh successful!");
        } catch (error) {
            console.error('Failed to trigger refresh:', error);
            loader.textContent = 'Error during refresh. Please try again.';
        } finally {
            // Update the leaderboard regardless of success/failure of the refresh
            await updateLeaderboardView();
            // Hide loader and re-enable button after a short delay
            setTimeout(() => {
                refreshButton.disabled = false;
                loader.style.display = 'none';
                loader.textContent = 'Fetching latest scores...'; // Reset text
            }, 1000);
        }
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
                    content.innerHTML = `
                        <span>${game.team1}</span>
                        <span style="font-weight:700; margin: 0 8px;">${game.score}</span>
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
            listEl.innerHTML = '<div>No data available. Click Refresh to fetch live data.</div>';
            return;
        }
        players.forEach((player, idx) => {
            const rowEl = document.createElement('div');
            let rowClass = 'player-row';
            if (idx === 0) rowClass += ' top1';
            else if (idx === 1) rowClass += ' top2';
            else if (idx === 2) rowClass += ' top3';
            rowEl.className = rowClass;
            rowEl.innerHTML = `
                <div class="player-rank">${idx + 1}</div>
                <div class="player-name" data-player="${player.name}">${player.name}</div>
                <div class="player-score">${player.score} pts</div>
            `;
            listEl.appendChild(rowEl);
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

        const sections = {
            '1/8 Final': createList(bets['1/8']),
            '1/4 Final': createList(bets['1/4']),
            '1/2 Final': createList(bets['1/2']),
            'Final': createList(bets['Final']),
            'Winner': createPara(bets.Winner),
            'Best Striker': createPara(bets.BestStriker, true)
        };

        const createSection = (title) => sections[title] ? `<div class="details-section"><h3>${title}</h3>${sections[title]}</div>` : '';

        const column1 = `<div class="details-column">${createSection('1/8 Final')}</div>`;
        const column2 = `<div class="details-column">${createSection('1/4 Final')}</div>`;
        const column3 = `<div class="details-column">${createSection('1/2 Final')}</div>`;
        const column4 = `<div class="details-column">${createSection('Final')}${createSection('Winner')}${createSection('Best Striker')}</div>`;

        detailsContent.innerHTML = column1 + column2 + column3 + column4;
        detailsPanel.classList.add('visible');
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
    });

    refreshButton.addEventListener('click', triggerRefresh);

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

    updateLeaderboardView();

    // Call on page load and every 30 seconds
    fetchLiveGame();
    setInterval(fetchLiveGame, 30000);

    async function renderTopScorers() {
        const list = document.getElementById('top-scorers-list');
        try {
            const res = await fetch('/api/top_scorers');
            const scorers = await res.json();
            list.innerHTML = `
                <ul>
                    ${scorers.map(s => `
                        <li>
                            <span class="data-col data-col-rank">${s.Rank}</span>
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
                    `).join('')}
                </ul>
            `;
        } catch (e) {
            list.innerHTML = '<div>Could not load top scorers.</div>';
        }
    }

    // Call this on page load
    renderTopScorers();
});