/**
 * CLAWDBOT Data Stream Background
 * Subtle flowing data particles — cyberpunk meets Lumon data visualization.
 * Less "heavy rain," more "ambient neural data flow."
 */
(function () {
  'use strict';

  var canvas = document.getElementById('data-stream');
  if (!canvas) return;
  var ctx = canvas.getContext('2d');

  // Character sets
  var katakana = [];
  for (var k = 0x30A0; k <= 0x30FF; k++) katakana.push(String.fromCharCode(k));
  var digits = '0123456789'.split('');
  var blocks = '\u2581\u2582\u2583\u2584\u2585\u2586\u2587\u2588'.split('');
  var charPool = katakana.concat(digits, blocks);

  // Config
  var FONT_SIZE = 13;
  var FADE_ALPHA = 0.03;
  var COL_DENSITY = 0.4; // only 40% of possible columns are active
  var COLORS = {
    primary: 'rgba(0, 240, 255, 0.25)',    // cyan, very dim
    secondary: 'rgba(138, 155, 174, 0.15)', // lumon steel
    lead: 'rgba(0, 240, 255, 0.6)',         // brighter lead char
    rare: 'rgba(255, 0, 170, 0.3)'          // occasional magenta
  };

  var columns = 0;
  var drops = [];
  var speeds = [];
  var activeColumns = [];

  function randomChar() {
    return charPool[Math.floor(Math.random() * charPool.length)];
  }

  function initColumns() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    columns = Math.floor(canvas.width / FONT_SIZE);
    drops = [];
    speeds = [];
    activeColumns = [];

    for (var i = 0; i < columns; i++) {
      drops[i] = Math.random() * -150;
      speeds[i] = 0.3 + Math.random() * 0.8;
      activeColumns[i] = Math.random() < COL_DENSITY;
    }
  }

  var lastFrame = 0;
  var FRAME_INTERVAL = 50; // ~20fps for subtle feel

  function draw(timestamp) {
    requestAnimationFrame(draw);
    if (timestamp - lastFrame < FRAME_INTERVAL) return;
    lastFrame = timestamp;

    // Fade trail
    ctx.fillStyle = 'rgba(5, 5, 8, ' + FADE_ALPHA + ')';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.font = FONT_SIZE + 'px monospace';

    for (var i = 0; i < columns; i++) {
      if (!activeColumns[i]) continue;

      var x = i * FONT_SIZE;
      var y = drops[i] * FONT_SIZE;

      if (y > 0 && y < canvas.height + FONT_SIZE) {
        var ch = randomChar();
        var rng = Math.random();

        // Color selection
        if (rng < 0.02) {
          ctx.fillStyle = COLORS.rare;
          ctx.shadowColor = 'rgba(255, 0, 170, 0.4)';
          ctx.shadowBlur = 8;
        } else if (rng < 0.1) {
          ctx.fillStyle = COLORS.lead;
          ctx.shadowColor = 'rgba(0, 240, 255, 0.3)';
          ctx.shadowBlur = 6;
        } else if (rng < 0.4) {
          ctx.fillStyle = COLORS.secondary;
          ctx.shadowBlur = 0;
        } else {
          ctx.fillStyle = COLORS.primary;
          ctx.shadowBlur = 0;
        }

        ctx.fillText(ch, x, y);
        ctx.shadowBlur = 0;
      }

      drops[i] += speeds[i];

      if (drops[i] * FONT_SIZE > canvas.height && Math.random() > 0.98) {
        drops[i] = Math.random() * -30;
        speeds[i] = 0.3 + Math.random() * 0.8;
        // Occasionally toggle column activity
        if (Math.random() < 0.1) activeColumns[i] = !activeColumns[i];
      }
    }
  }

  initColumns();
  requestAnimationFrame(draw);

  var resizeTimer;
  window.addEventListener('resize', function () {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function () {
      initColumns();
      ctx.fillStyle = 'rgba(5, 5, 8, 1)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
    }, 200);
  });
})();
