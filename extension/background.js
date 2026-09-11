chrome.tabs.onActivated.addListener(async () => {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab) return;

    const payload = {
      title: tab.title || null,
      url: tab.url || null,
      active: true,
      timestamp: Date.now(),
    };

    console.log('Locus browser context:', payload);
  } catch (error) {
    console.error('Locus extension error:', error);
  }
});
