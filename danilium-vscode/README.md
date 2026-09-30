# Danilium Language Support for VS Code

This minimal extension associates `.dnl` files with Danilium and provides TextMate syntax highlighting. It does not include an LSP, diagnostics, autocomplete, or a formatter.

## Try it from the repository

From the Danilium repository root, run:

```bash
code --extensionDevelopmentPath=./danilium-vscode .
```

This opens an Extension Development Host with the extension loaded. Open any `.dnl` file to see highlighting.

## Included editor support

- `.dnl` file recognition
- Danilium control-flow and function keywords
- Boolean literals, strings, escapes, and numbers
- Comments beginning with `#`
- Operators, function calls, and basic bracket/indent handling

## Package for local installation

Install `@vscode/vsce`, then run `vsce package` from this directory. This creates a `.vsix` file that can be installed with `code --install-extension <file>.vsix`.
