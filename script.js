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

        const createPara = (bet) => {
            if (!bet || !bet.team) return '';
            return `<p class="status-${bet.status}">${bet.team}</p>`;
        };

        const sections = {
            '1/8 Final': createList(bets['1/8']),
            '1/4 Final': createList(bets['1/4']),
            '1/2 Final': createList(bets['1/2']),
            'Final': createList(bets['Final']),
            'Winner': createPara(bets.Winner),
            'Best Striker': createPara(bets.BestStriker)
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
});