# Contributing Guidelines

How to contribute to the Server Building Dashboard.

## Getting Started

1. **Fork the repository** (if external contributor)
2. **Clone your fork**
   ```bash
   git clone <your-fork-url>
   cd server-building-dashboard
   ```
3. **Set up development environment**
   ```bash
   # See Development Guide for full setup
   ./docker.sh dev start
   ```

## Development Workflow

### 1. Create a Branch

```bash
# Update main
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/your-feature-name
```

### Branch Naming

| Type | Format | Example |
|------|--------|---------|
| Feature | `feature/description` | `feature/add-bulk-assign` |
| Bug Fix | `fix/description` | `fix/login-redirect-loop` |
| Documentation | `docs/description` | `docs/api-examples` |
| Refactor | `refactor/description` | `refactor/auth-module` |
| Test | `test/description` | `test/preconfig-endpoint` |

### 2. Make Changes

- Write clear, focused commits
- Follow code style guidelines
- Add tests for new functionality
- Update documentation

### 3. Test Your Changes

```bash
# Backend tests
cd backend
docker run --rm \
  -v "$(pwd)/tests:/app/tests:ro" \
  server-dashboard-backend-test:latest \
  pytest -v

# Frontend type check
npm run typecheck

# Frontend lint
npm run lint
```

### 4. Commit Changes

Follow conventional commits:

```bash
# Format: <type>(<scope>): <description>

git commit -m "feat(preconfig): add bulk push support"
git commit -m "fix(auth): resolve session timeout issue"
git commit -m "docs(api): add preconfig endpoint examples"
git commit -m "test(assign): add permission tests"
git commit -m "refactor(hooks): simplify useBuildStatus"
```

#### Commit Types

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation |
| `test` | Tests |
| `refactor` | Code refactoring |
| `style` | Formatting (no logic change) |
| `perf` | Performance improvement |
| `chore` | Build, tooling, etc. |

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub/GitLab.

## Pull Request Guidelines

### PR Title

Use conventional commit format:
```
feat(preconfig): add bulk push support
```

### PR Description

```markdown
## Summary
Brief description of changes.

## Changes
- Added X functionality
- Fixed Y bug
- Updated Z documentation

## Testing
- [ ] Backend tests pass
- [ ] Frontend typecheck passes
- [ ] Manually tested in dev mode

## Screenshots
(If UI changes)

## Notes
Any additional context.
```

### Review Process

1. **Automated checks** run (tests, linting)
2. **Code review** by maintainer
3. **Address feedback** if needed
4. **Merge** when approved

## Code Style

### TypeScript/React

```typescript
// Use TypeScript strictly
interface Props {
  name: string;
  count: number;
  onClick?: () => void;
}

// Functional components with default export
export default function MyComponent({ name, count }: Props) {
  return <div>{name}: {count}</div>;
}

// Custom hooks with use prefix
function useMyHook() {
  const [state, setState] = useState<string>('');
  return { state, setState };
}
```

### Python/FastAPI

```python
# Type hints everywhere
def get_user(user_id: str) -> User:
    """Get user by ID.

    Args:
        user_id: The user's unique identifier.

    Returns:
        The User object.

    Raises:
        HTTPException: If user not found.
    """
    user = find_user(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return user

# Pydantic models for validation
class CreateUserRequest(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=100)
```

### Formatting

```bash
# Backend
black .
ruff check --fix .

# Frontend
npm run lint
```

## Documentation

### When to Update Docs

| Change | Documentation |
|--------|---------------|
| New API endpoint | `docs/api/` |
| New feature | `docs/features/` |
| Config changes | `docs/getting-started/configuration.md` |
| Architecture changes | `docs/architecture/` |
| Security changes | `docs/security/` |

### Documentation Style

- Use clear, concise language
- Include code examples
- Add tables for structured data
- Use Mermaid for diagrams
- Link to related documentation

## Testing Requirements

### Backend

- All new endpoints need tests
- Cover success and error cases
- Test permission boundaries
- Maintain 80% coverage

### Frontend

- (Future) Component tests for new components
- Verify TypeScript types
- Test with mock data

## Reporting Issues

### Bug Report

```markdown
## Description
Clear description of the bug.

## Steps to Reproduce
1. Go to '...'
2. Click on '...'
3. See error

## Expected Behavior
What should happen.

## Actual Behavior
What actually happens.

## Environment
- Browser: Chrome 120
- OS: macOS 14
- Version: 1.0.0

## Screenshots
(If applicable)

## Additional Context
Any other relevant information.
```

### Feature Request

```markdown
## Summary
Brief description of the feature.

## Motivation
Why is this feature needed?

## Proposed Solution
How should it work?

## Alternatives Considered
Other approaches considered.

## Additional Context
Any other relevant information.
```

## Security Issues

**Do not open public issues for security vulnerabilities.**

1. Email the security team privately
2. Include detailed reproduction steps
3. Allow time for remediation before disclosure

## Questions?

- Check existing documentation
- Search closed issues
- Open a discussion topic
- Ask in team channel

## License

By contributing, you agree that your contributions will be licensed under the project's license.

## Thank You!

We appreciate your contributions to make this project better!
