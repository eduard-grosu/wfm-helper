let additionalInfo = {};
let currentUrl = window.location.href;
let urlCheckTimeout;

// warframe.market/profile/username
const urlPattern = /\/profile\/[^/]+$/;

const checkUrlChange = () => {
    if (window.location.href !== currentUrl) {
        currentUrl = window.location.href;
        console.log("URL changed to:", currentUrl);

        if (urlPattern.test(currentUrl)) {
            window.location.reload();
        }
    }
};

const addExtraInfo = (order) => {
    // todo: do not rely on random class names
    const nameContainer = order.querySelector('.order-unit__item-name--QNXKh');
    if (!nameContainer) return;

    const nameSpan = nameContainer.querySelector('span');
    const ducats = additionalInfo[nameSpan.textContent];
    if (!ducats || order.querySelector('.extra-info')) return;

    const platinumContainer = order.querySelector('.price--LQgqJ.sell--UxmH0 b');
    const platinum = parseInt(platinumContainer.textContent);

    let color;
    if ((ducats >= 45 && platinum === 1) || (ducats >= 90 && platinum <= 2)) {
        color = '#ffd700'; // gold
    } else {
        color = ducats >= 45 ? '#90ee90' : '#ff6666'; // green or red
    }

    const extraInfoSpan = document.createElement('span');
    extraInfoSpan.style.color = color;
    extraInfoSpan.textContent = `${ducats} ducats`;

    nameContainer.appendChild(document.createTextNode(' - '));
    nameContainer.appendChild(extraInfoSpan);
}

const observeOrdersContainer = () => {
    const observer = new MutationObserver((mutationsList) => {
        for (let mutation of mutationsList) {
            if (mutation.type === 'childList') {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === Node.ELEMENT_NODE && node.tagName === 'DIV') {
                        addExtraInfo(node);
                    }
                });
            }
        }

        clearTimeout(urlCheckTimeout);
        urlCheckTimeout = setTimeout(checkUrlChange, 100);
    });

    observer.observe(document.body, { childList: true, subtree: true });
}

setTimeout(() => {
    fetch(chrome.runtime.getURL('data/components.json'))
        .then(response => response.json())
        .then(data => {
            additionalInfo = data;
            document.querySelectorAll('.order-unit--GERZ4').forEach(addExtraInfo);
            observeOrdersContainer();
            window.addEventListener('popstate', checkUrlChange);
        })
        .catch(error => console.error('Error:', error));
}, 500);
