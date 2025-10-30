import prettier from "eslint-plugin-prettier";
import jsdoc from "eslint-plugin-jsdoc";
import react from "eslint-plugin-react";
import reactHooks from "eslint-plugin-react-hooks";

export default [
  {
    ignores: ["dist/*", "build/*", "node_modules/*"],
  },
  {
    files: ["**/*.{js,jsx,mjs,cjs,ts,tsx}"],
    plugins: {
      prettier,
      jsdoc,
      react,
      "react-hooks": reactHooks,
    },
    languageOptions: {
      ecmaVersion: 2024,
      sourceType: "module",
      parserOptions: {
        ecmaFeatures: {
          jsx: true,
        },
      },
    },
    settings: {
      react: {
        version: "detect",
      },
      jsdoc: {
        mode: "typescript",
      },
    },
    rules: {
      // General ESLint rules
      "max-len": [
        "error",
        {
          code: 90,
        },
      ],
      camelcase: 0,
      "prefer-const": 0,
      quotes: [0, "single", "double"],
      "linebreak-style": 0,
      // Prettier integration
      "prettier/prettier": [
        "error",
        {
          endOfLine: "auto",
          trailingComma: "es5",
        },
      ],
      // React rules
      "react/react-in-jsx-scope": "off",
      "react/prop-types": "off",
      // React Hooks rules
      "react-hooks/rules-of-hooks": "error",
      "react-hooks/exhaustive-deps": "warn",
      // JSDoc rules
      "jsdoc/require-param-description": "off",
      "jsdoc/require-returns-description": "off",
    },
  },
];
