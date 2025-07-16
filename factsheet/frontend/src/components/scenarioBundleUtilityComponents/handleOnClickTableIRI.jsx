// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
//
// SPDX-License-Identifier: AGPL-3.0-or-later

// enhance open url function to handle urls better
// TODO change once OEKG is migrated
const handleOpenURL = (url, setError) => {
    if (!url || url.trim() === '') {
      setError('Invalid URL');
      return;
    }

    let processedURL = url.trim();

    // Handle URLs with spaces in the middle
    processedURL = processedURL.replace(/\s+/g, '%20');

    // Prepend base URL if not starting with http:// or https://
    if (!processedURL.startsWith('http://') && !processedURL.startsWith('https://')) {
      if (!processedURL.startsWith('/') )
        processedURL = "/" + processedURL;

      const baseURL = window.location.origin;
      processedURL = `${baseURL}${processedURL}`;
    }

    if (processedURL.startsWith('http://') && !processedURL.startsWith('http://127') && !processedURL.startsWith('http://local')){
      processedURL = processedURL.replace('http://', 'https://');
    }

    // Encode the URL to handle special characters
    try {
      const encodedURL = encodeURI(processedURL);
      window.open(encodedURL, "_blank");
    } catch (error) {
      setError('Invalid URL format');
    }
  };


export default handleOpenURL;
