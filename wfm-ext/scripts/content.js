let additionalInfo = {};
let currentUrl = window.location.href;
let urlCheckTimeout;

// warframe.market/profile/username
const urlPattern = /\/profile\/[^/]+$/;

const updateAllOrdersDucatInfo = () => {
    document.querySelectorAll('.order-unit--GERZ4').forEach(updateOrderDucatInfo);
}

const checkUrlChange = () => {
    if (window.location.href !== currentUrl) {
        currentUrl = window.location.href;
        console.log("URL changed to:", currentUrl);

        if (urlPattern.test(currentUrl)) {
            updateAllOrdersDucatInfo();
        }
    }
};

const updateOrderDucatInfo = (order) => {
    // todo: do not rely on random class names
    const nameContainer = order.querySelector('.order-unit__item-name--QNXKh');
    if (!nameContainer || order.querySelector('.ducat-info-1337')) return;

    const nameSpan = nameContainer.querySelector('span');
    const ducats = additionalInfo[nameSpan.textContent];

    const platinumContainer = order.querySelector('.price--LQgqJ.sell--UxmH0');
    if (!ducats || !platinumContainer) return;
    const platinum = parseInt(platinumContainer.textContent);

    let color;
    if ((ducats >= 45 && platinum === 1) || (ducats >= 90 && platinum <= 2)) {
        color = '#ffd700'; // gold
    } else {
        color = ducats >= 45 ? '#90ee90' : '#ff6666'; // green or red
    }

    const ducatInfoSpan = document.createElement('span');
    ducatInfoSpan.className = 'ducat-info-1337'
    ducatInfoSpan.style.color = color;
    ducatInfoSpan.textContent = `${ducats} ducats`;

    nameContainer.appendChild(document.createTextNode(' - '));
    nameContainer.appendChild(ducatInfoSpan);
}

const observeAllOrders = () => {
    const observer = new MutationObserver((mutationsList) => {
        for (let mutation of mutationsList) {
            if (mutation.type === 'childList') {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === Node.ELEMENT_NODE && node.tagName === 'DIV') {
                        updateOrderDucatInfo(node);
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
            updateAllOrdersDucatInfo();
            observeAllOrders();
            window.addEventListener('popstate', checkUrlChange);
        })
        .catch(error => console.error('Error:', error));
}, 500);
