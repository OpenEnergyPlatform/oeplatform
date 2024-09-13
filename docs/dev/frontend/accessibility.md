# Accessibility

## Why does it matter?

About [16 % of the world population :fontawesome-solid-arrow-up-right-from-square:](https://www.who.int/news-room/fact-sheets/detail/disability-and-health#:~:text=Key%20facts,1%20in%206%20of%20us.){:target="_blank"} experience some kind of disability. By making the Open Energy platform more accessible, we want to support open science and open data, ensuring that research and data are available to all, including individuals with disabilities. This will help not only to broaden the reach of our work but also to give the energy system research community a new range of different perspectives.

While the primary responsibility for accessibility lies with the design team, it is important that all members try to integrate accessibility into their workflow.

This documentation is a work in progress. We are continually striving to improve our accessibility standards and welcome feedback to help us achieve this goal.

## Assessment

Working on accessibilty often means using automation tools to support manual testing.

### Automated Testing

- Use [WAVE :fontawesome-solid-arrow-up-right-from-square:](https://wave.webaim.org/){:target="_blank"} as the main tool
- Use Lighthouse in the developer tools as a secondary tool
- It is of course possible to use other tools:
    - [BrowserStack :fontawesome-solid-arrow-up-right-from-square:](https://www.browserstack.com/accessibility-testing){:target="_blank"} (needs paid account)
    - Browser extensions such as [Accessibility Insights :fontawesome-solid-arrow-up-right-from-square:](https://accessibilityinsights.io/docs/web/getstarted/assessment/){:target="_blank"}

### Manual Testing

#### General

- General tips
    - For [designers :fontawesome-solid-arrow-up-right-from-square:](https://www.w3.org/WAI/tips/designing/){:target="_blank"}
    - For [developers :fontawesome-solid-arrow-up-right-from-square:](https://www.w3.org/WAI/tips/developing/){:target="_blank"}
    - For [content writers :fontawesome-solid-arrow-up-right-from-square:](https://www.w3.org/WAI/tips/writing/){:target="_blank"}
        - Includes platform and documentation
- Color:
    - Verify text color contrast
        - [Contrast Checker :fontawesome-solid-arrow-up-right-from-square:](https://webaim.org/resources/contrastchecker/){:target="_blank"}
    - Ensure that color is not the only means of conveying information
- Correct HTML and headings structure
    - [Tutorial :fontawesome-solid-arrow-up-right-from-square:](https://www.w3.org/WAI/tutorials/page-structure/){:target="_blank"}
- Appropriate use of ARIA roles and landmarks
    - [Directives :fontawesome-solid-arrow-up-right-from-square:](https://www.w3.org/WAI/ARIA/apg/patterns/){:target="_blank"} for different components
- Forms and Labels
    - [Tutorial :fontawesome-solid-arrow-up-right-from-square:](https://www.w3.org/WAI/tutorials/forms/){:target="_blank"}
- Images and Media
    - [Tutorial :fontawesome-solid-arrow-up-right-from-square:](https://www.w3.org/WAI/tutorials/images/){:target="_blank"}
    - Transcripts or captions for audio and video content
- Menus
    - [Tutorial :fontawesome-solid-arrow-up-right-from-square:](https://www.w3.org/WAI/tutorials/menus/){:target="_blank"}
- Tables
    - [Tutorial :fontawesome-solid-arrow-up-right-from-square:](https://www.w3.org/WAI/tutorials/tables/){:target="_blank"}
- Video Media
    - [Resource :fontawesome-solid-arrow-up-right-from-square:](https://www.w3.org/WAI/media/av/){:target="_blank"}

#### Keyboard Testing

[Techniques :fontawesome-solid-arrow-up-right-from-square:](https://webaim.org/techniques/keyboard/){:target="_blank"}

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