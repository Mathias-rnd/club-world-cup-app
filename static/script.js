// script.js

// Team logos mapping - using ESPN CDN sources only
const TEAM_LOGOS = {
    'Al Hilal': 'https://a.espncdn.com/i/teamlogos/soccer/500/929.png',
    'América': 'https://a.espncdn.com/i/teamlogos/soccer/500/227.png',
    'Bayern München': 'https://a.espncdn.com/i/teamlogos/soccer/500/132.png',
    'SL Benfica': 'https://a.espncdn.com/i/teamlogos/soccer/500/1929.png',
    'Borussia Dortmund': 'https://a.espncdn.com/i/teamlogos/soccer/500/124.png',
    'Botafogo - RJ': 'https://a.espncdn.com/i/teamlogos/soccer/500/6086.png',
    'Chelsea FC': 'https://a.espncdn.com/i/teamlogos/soccer/500/363.png',
    'FC Porto': 'https://a.espncdn.com/i/teamlogos/soccer/500/437.png',
    'Flamengo RJ': 'https://a.espncdn.com/i/teamlogos/soccer/500/819.png',
    'Fluminense': 'https://a.espncdn.com/i/teamlogos/soccer/500/3445.png',
    'Fluminense RJ': 'https://a.espncdn.com/i/teamlogos/soccer/500/3445.png',
    'Inter Miami CF': 'https://a.espncdn.com/i/teamlogos/soccer/500/20232.png',
    'Inter': 'https://a.espncdn.com/i/teamlogos/soccer/500/110.png',
    'Juventus': 'https://a.espncdn.com/i/teamlogos/soccer/500/111.png',
    'Manchester City': 'https://a.espncdn.com/i/teamlogos/soccer/500/382.png',
    'CF Monterrey': 'https://a.espncdn.com/i/teamlogos/soccer/500/220.png',
    'Palmeiras': 'https://a.espncdn.com/i/teamlogos/soccer/500/2029.png',
    'Paris Saint-Germain': 'https://a.espncdn.com/i/teamlogos/soccer/500/160.png',
    'Real Madrid': 'https://a.espncdn.com/i/teamlogos/soccer/500/86.png',
    'River Plate': 'https://a.espncdn.com/i/teamlogos/soccer/500/16.png',
    'Boca Juniors': 'https://a.espncdn.com/i/teamlogos/soccer/500/5.png',
    'Salzburg': 'https://a.espncdn.com/i/teamlogos/soccer/500/2790.png',
    'Atletico Madrid': 'https://a.espncdn.com/i/teamlogos/soccer/500/1068.png',
    'Los Angeles FC': 'https://a.espncdn.com/i/teamlogos/soccer/500/18966.png',
};

function getTeamLogo(teamName) {
    return TEAM_LOGOS[teamName] || null;
}

function createTeamDisplay(teamName) {
    const logo = getTeamLogo(teamName);
    if (logo) {
        return `<div class="team-with-logo">
                    <img src="${logo}" alt="${teamName}" class="team-logo" onerror="this.style.display='none'">
                    <span>${teamName}</span>
                </div>`;
    }
    return `<span>${teamName}</span>`;
}

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
                        <div class="live-game-teams">
                            ${createTeamDisplay(game.team1)}
                            <span class="live-game-score">${formattedScore}</span>
                            ${createTeamDisplay(game.team2)}
                        </div>
                    `;
                } else {
                    // Game has not started yet
                    container.style.display = 'block';
                    header.innerHTML = game.date ? `Next game – ${game.date}` : `Next game`;
                    // Show the time if available, else just show teams
                    let timeStr = '';
                    if (game.time) {
                        // Add 1 hour to account for timezone difference
                        const timeParts = game.time.split(':');
                        if (timeParts.length === 2) {
                            let hour = parseInt(timeParts[0]);
                            const minute = timeParts[1];
                            hour = (hour + 1) % 24; // Add 1 hour and handle 24-hour format
                            const adjustedTime = `${hour.toString().padStart(2, '0')}:${minute}`;
                            timeStr = `<div class="live-game-time">${adjustedTime}</div>`;
                        } else {
                            timeStr = `<div class="live-game-time">${game.time}</div>`;
                        }
                    }
                    content.innerHTML = `
                        ${timeStr}
                        <div class="live-game-teams">
                            ${createTeamDisplay(game.team1)}
                            <span class="live-game-vs">vs</span>
                            ${createTeamDisplay(game.team2)}
                        </div>
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

        // Helper function to create team display with logo
        function createTeamDisplay(teamName) {
            const logo = getTeamLogo(teamName);
            if (logo) {
                return `<div class="team-with-logo">
                            <img src="${logo}" alt="${teamName}" class="team-logo" onerror="this.style.display='none'">
                            <span>${teamName}</span>
                        </div>`;
            }
            return `<span>${teamName}</span>`;
        }

        // Helper function to create a list of bets
        function createBetList(betArray, title) {
            if (!betArray || betArray.length === 0) return '';
            const items = betArray.map(bet => {
                const teamDisplay = createTeamDisplay(bet.team);
                // Ensure status is valid, fallback to pending if not
                const status = bet.status && ['pending', 'correct', 'incorrect', 'partial', 'live-correct', 'live-wrong', 'live-pending'].includes(bet.status) 
                    ? bet.status 
                    : 'pending';
                return `<li class="status-${status}">${teamDisplay}</li>`;
            }).join('');
            return `<div class="bet-section">
                        <h3>${title}</h3>
                        <ul>${items}</ul>
                    </div>`;
        }

        // Helper function to create single bet display
        function createSingleBet(bet, title) {
            if (!bet || !bet.team) return '';
            const teamDisplay = createTeamDisplay(bet.team);
            // Ensure status is valid, fallback to pending if not
            const status = bet.status && ['pending', 'correct', 'incorrect', 'partial', 'live-correct', 'live-wrong', 'live-pending'].includes(bet.status) 
                ? bet.status 
                : 'pending';
            return `<div class="bet-section">
                        <h3>${title}</h3>
                        <ul><li class="status-${status}">${teamDisplay}</li></ul>
                    </div>`;
        }

        // Helper function to create joker section
        function createJokerSection(jokers, title) {
            if (!jokers || jokers.length === 0) return '';
            
            const jokerItems = jokers
                .map((joker, index) => {
                    if (!joker || !joker.team || !joker.team.trim()) return null;
                    const pointsText = joker.points !== undefined ? ` (${joker.points > 0 ? '+' : ''}${joker.points} pts)` : '';
                    // Ensure status is valid, fallback to pending if not
                    const status = joker.status && ['pending', 'correct', 'incorrect', 'partial', 'live-correct', 'live-wrong', 'live-pending'].includes(joker.status) 
                        ? joker.status 
                        : 'pending';
                    return `<li class="status-${status}">Joker ${index + 1}: ${joker.team}${pointsText}</li>`;
                })
                .filter(item => item !== null);
            
            if (jokerItems.length === 0) return '';
            return `<div class="bet-section">
                        <h3>${title} Jokers</h3>
                        <ul>${jokerItems.join('')}</ul>
                    </div>`;
        }

        // Build the content with horizontal layout
        let content = '<div class="bet-details-grid">';
        
        // Column 1: Round of 16
        content += '<div class="bet-column">';
        content += createBetList(bets['1/8'], 'Round of 16');
        if (bets.Jokers && bets.Jokers['1/8']) {
            content += createJokerSection(bets.Jokers['1/8'], 'Round of 16');
        }
        content += '</div>';
        
        // Column 2: Quarter Finals
        content += '<div class="bet-column">';
        content += createBetList(bets['1/4'], 'Quarter Finals');
        if (bets.Jokers && bets.Jokers['1/4']) {
            content += createJokerSection(bets.Jokers['1/4'], 'Quarter Finals');
        }
        content += '</div>';
        
        // Column 3: Semi Finals
        content += '<div class="bet-column">';
        content += createBetList(bets['1/2'], 'Semi Finals');
        if (bets.Jokers && bets.Jokers['1/2']) {
            content += createJokerSection(bets.Jokers['1/2'], 'Semi Finals');
        }
        content += '</div>';
        
        // Column 4: Final, Winner, Best Striker
        content += '<div class="bet-column">';
        content += createBetList(bets['Final'], 'Final');
        content += createSingleBet(bets.Winner, 'Winner');
        content += createSingleBet(bets.BestStriker, 'Best Striker');
        content += '</div>';
        
        content += '</div>';

        detailsContent.innerHTML = content;
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

    // Keep live game and top scorers updated every 30 seconds
    setInterval(fetchLiveGame, 30000);
    setInterval(renderTopScorers, 30000);
});