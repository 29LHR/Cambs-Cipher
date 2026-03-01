// Caesar shift function preserving case and non-letters
function caesarShift(text, shift) {
  const aCode = 'a'.charCodeAt(0);
  const ACode = 'A'.charCodeAt(0);
  const out = [];
  const s = ((shift % 26) + 26) % 26;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    const code = text.charCodeAt(i);
    if (code >= ACode && code <= ACode + 25) {
      out.push(String.fromCharCode(((code - ACode + s) % 26) + ACode));
    } else if (code >= aCode && code <= aCode + 25) {
      out.push(String.fromCharCode(((code - aCode + s) % 26) + aCode));
    } else {
      out.push(ch);
    }
  }
  return out.join('');
}

function applyCipher() {
  const input = document.getElementById('inputText').value || '';
  const shiftVal = parseInt(document.getElementById('shift').value || '0', 10);
  const mode = document.getElementById('mode').value;
  const shift = mode === 'decode' ? -shiftVal : shiftVal;
  document.getElementById('output').textContent = caesarShift(input, shift);
  document.getElementById('bruteResults').innerHTML = '';
}

function doBruteForce() {
  const input = document.getElementById('inputText').value || '';
  const container = document.getElementById('bruteResults');
  container.innerHTML = '';
  if (!input) {
    container.textContent = 'Enter text to run brute force.';
    return;
  }
  const list = document.createElement('div');
  list.className = 'example-box';
  for (let k = 1; k <= 25; k++) {
    const shifted = caesarShift(input, -k);
    const p = document.createElement('div');
    p.textContent = `Shift ${k}: ${shifted}`;
    list.appendChild(p);
  }
  container.appendChild(list);
}

// Attach event listeners after DOM is ready
(function () {
  function safeGet(id) { return document.getElementById(id); }

  const waitFor = function (fn) {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', fn);
    } else {
      fn();
    }
  };

  waitFor(() => {
    const applyBtn = safeGet('applyBtn');
    if (applyBtn) applyBtn.addEventListener('click', applyCipher);

    const bruteBtn = safeGet('bruteBtn');
    if (bruteBtn) bruteBtn.addEventListener('click', doBruteForce);

    const copyBtn = safeGet('copyBtn');
    if (copyBtn) copyBtn.addEventListener('click', async () => {
      const text = (safeGet('output') && safeGet('output').textContent) || '';
      try {
        await navigator.clipboard.writeText(text);
        alert('Copied to clipboard');
      } catch (e) {
        alert('Copy failed — select and copy manually.');
      }
    });

    const clearBtn = safeGet('clearBtn');
    if (clearBtn) clearBtn.addEventListener('click', () => {
      if (safeGet('inputText')) safeGet('inputText').value = '';
      if (safeGet('output')) safeGet('output').textContent = '';
      if (safeGet('bruteResults')) safeGet('bruteResults').innerHTML = '';
    });

    const inputText = safeGet('inputText');
    if (inputText) inputText.addEventListener('input', applyCipher);

    const shift = safeGet('shift');
    if (shift) shift.addEventListener('change', applyCipher);

    const mode = safeGet('mode');
    if (mode) mode.addEventListener('change', applyCipher);
  });
})();
