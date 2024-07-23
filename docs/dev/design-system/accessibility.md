# Accessibility

## Why does it matter?

About [16 % of the world population](https://www.who.int/news-room/fact-sheets/detail/disability-and-health#:~:text=Key%20facts,1%20in%206%20of%20us.) experience some kind of disability. By making the Open Energy platform more accessible, we want to support open science and open data, ensuring that research and data are available to all, including individuals with disabilities. This will help not only to broaden the reach of our work but also to give the energy system research community a new range of different perspectives.

While the primary responsibility for accessibility lies with the design team, it is important that all members try to integrate accessibility into their workflow.

This documentation is a work in progress. We are continually striving to improve our accessibility standards and welcome feedback to help us achieve this goal.

## Assessment

Working on accessibilty often means using automation tools to support manual testing.

### Automated Testing

- Use [WAVE](https://wave.webaim.org/) as the main tool
- Use Lighthouse in the developer tools as a secondary tool
- It is of course possible to use other tools:
    - [BrowserStack](https://www.browserstack.com/accessibility-testing) (needs paid account)
    - Browser extensions such as [Accessibility Insights](https://accessibilityinsights.io/docs/web/getstarted/assessment/)

### Manual Testing

#### General

- General tips
    - For [designers](https://www.w3.org/WAI/tips/designing/)
    - For [developers](https://www.w3.org/WAI/tips/developing/)
    - For [content writers](https://www.w3.org/WAI/tips/writing/)
        - Includes platform and documentation
- Color:
    - Verify text color contrast
        - [Contrast Checker](https://webaim.org/resources/contrastchecker/)
    - Ensure that color is not the only means of conveying information
- Correct HTML and headings structure
    - [Tutorial](https://www.w3.org/WAI/tutorials/page-structure/)
- Appropriate use of ARIA roles and landmarks
    - [Directives](https://www.w3.org/WAI/ARIA/apg/patterns/) for different components
- Forms and Labels
    - [Tutorial](https://www.w3.org/WAI/tutorials/forms/)
- Images and Media
    - [Tutorial](https://www.w3.org/WAI/tutorials/images/)
    - Transcripts or captions for audio and video content
- Menus
    - [Tutorial](https://www.w3.org/WAI/tutorials/menus/)
- Tables
    - [Tutorial](https://www.w3.org/WAI/tutorials/tables/)
- Video Media
    - [Resource](https://www.w3.org/WAI/media/av/)

#### Keyboard Testing

[Techniques](https://webaim.org/techniques/keyboard/)

#### Screen Reader Testing

- Use screen readers like NVDA (Windows), VoiceOver (Mac/iOS), and TalkBack (Android) or use a tool such as BrowserStack
- Familiarize with Shortcuts
- Check the following (mostly covered in the "General" section):
    - Headings structure
    - ARIA landmarks
    - ARIA live regions for dynamic content updates
    - Alt attributes
    - Descriptive texts for links and buttons
    - Form labels
    - Modal dialogs
    - Menus and dropdowns
    - Tables

### User Testing

Conduct usability testing sessions with users who have various disabilities (visual, auditory, motor, cognitive)‚

## Remediation

- Implement fixes
- Continuous monitoring
- Team training