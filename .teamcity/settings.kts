import jetbrains.buildServer.configs.kotlin.*
import jetbrains.buildServer.configs.kotlin.buildFeatures.commitStatusPublisher
import jetbrains.buildServer.configs.kotlin.buildFeatures.perfmon
import jetbrains.buildServer.configs.kotlin.buildFeatures.vcsLabeling
import jetbrains.buildServer.configs.kotlin.buildSteps.DockerCommandStep
import jetbrains.buildServer.configs.kotlin.buildSteps.Qodana
import jetbrains.buildServer.configs.kotlin.buildSteps.dockerCommand
import jetbrains.buildServer.configs.kotlin.buildSteps.python
import jetbrains.buildServer.configs.kotlin.buildSteps.qodana
import jetbrains.buildServer.configs.kotlin.buildSteps.script
import jetbrains.buildServer.configs.kotlin.failureConditions.BuildFailureOnMetric
import jetbrains.buildServer.configs.kotlin.failureConditions.failOnMetricChange
import jetbrains.buildServer.configs.kotlin.projectFeatures.dockerRegistry
import jetbrains.buildServer.configs.kotlin.projectFeatures.githubAppConnection
import jetbrains.buildServer.configs.kotlin.projectFeatures.githubIssues
import jetbrains.buildServer.configs.kotlin.triggers.vcs
import jetbrains.buildServer.configs.kotlin.vcs.GitVcsRoot

/*
The settings script is an entry point for defining a TeamCity
project hierarchy. The script should contain a single call to the
project() function with a Project instance or an init function as
an argument.

VcsRoots, BuildTypes, Templates, and subprojects can be
registered inside the project using the vcsRoot(), buildType(),
template(), and subProject() methods respectively.

To debug settings scripts in command-line, run the

    mvnDebug org.jetbrains.teamcity:teamcity-configs-maven-plugin:generate

command and attach your debugger to the port 8000.

To debug in IntelliJ Idea, open the 'Maven Projects' tool window (View
-> Tool Windows -> Maven Projects), find the generate task node
(Plugins -> teamcity-configs -> teamcity-configs:generate), the
'Debug' option is available in the context menu for the task.
*/

version = "2025.11"

project {
    description = "The Dedicated Server Docker build for Vintage Story"

    vcsRoot(HttpsGithubComDarkMatterProductionsVintagestoryRefsHeadsFeaturesWildcard)

    buildType(IntegrateAndPublish)
    buildType(BuildFeature_1)
    buildType(IntegrateRelease)
    buildType(RunTestsAndLinting)

    params {
        param("teamcity.internal.pipelines.creation.enabled", "true")
    }

    features {
        dockerRegistry {
            id = "PROJECT_EXT_3"
            name = "Docker Registry"
            userName = "ralnoc"
            password = "credentialsJSON:c4a4ea2b-4912-4165-979c-4eea6c95fa27"
        }
        githubIssues {
            id = "PROJECT_EXT_5"
            displayName = "DarkMatterProductions/vintagestory"
            repositoryURL = "https://github.com/DarkMatterProductions/vintagestory"
            authType = storedToken {
                tokenId = "tc_token_id:CID_5653b11f0397ee3bd028d13e6ac13958:-1:e9bb50ed-f183-4c1a-8607-254d0258ca3a"
            }
        }
        githubAppConnection {
            id = "PROJECT_EXT_8"
            displayName = "DMP - TeamCity"
            appId = "2881366"
            clientId = "Iv23liwMMBIfVOA9jezE"
            clientSecret = "credentialsJSON:7ecef34b-67cb-41ce-817e-1ffde3408d4c"
            privateKey = "credentialsJSON:d0a6df14-b64d-4e7f-9106-4d8a3d387861"
            ownerUrl = "https://github.com/DarkMatterProductions"
            useUniqueCallback = true
        }
    }
}

object BuildFeature_1 : BuildType({
    id("BuildFeature")
    name = "Build Feature"

    maxRunningBuildsPerBranch = "*:1"

    params {
        param("build.version.docker.new", "")
    }

    outputParams {
        exposeAllParameters = false
    }

    vcs {
        root(DslContext.settingsRoot)

        cleanCheckout = true
        branchFilter = "+:refs/heads/feature/*"
    }

    steps {
        script {
            name = "Setup Python"
            id = "Setup_Python"
            scriptContent = """
                #!/usr/bin/env bash
                
                pipenv install pyyaml
            """.trimIndent()
        }
        python {
            name = "Generate Version"
            id = "python_runner"
            environment = pipenv {
            }
            command = file {
                filename = "semver.py"
                scriptArguments = "--name vsvanillaplus --dev --no-build"
            }
        }
        dockerCommand {
            name = "Build Docker Image"
            id = "DockerCommand"
            commandType = build {
                source = file {
                    path = "Dockerfile"
                }
                platform = DockerCommandStep.ImagePlatform.Linux
                namesAndTags = "registry.dmpsys.in/vintagestory:%build.version.docker.new%"
            }
        }
        dockerCommand {
            name = "Push Docker Image"
            id = "Push_Docker_Image"
            commandType = push {
                namesAndTags = "registry.dmpsys.in/vintagestory:%build.version.docker.new%"
            }
        }
        dockerCommand {
            name = "Docker Prune"
            id = "Docker_Prune"
            executionMode = BuildStep.ExecutionMode.ALWAYS
            commandType = other {
                subCommand = "system"
                commandArgs = "prune"
            }
        }
        script {
            name = "Cleanup Python"
            id = "Cleanup_Python"
            scriptContent = """
                #!/usr/bin/env bash
                
                pipenv --rm
            """.trimIndent()
        }
    }

    triggers {
        vcs {
            branchFilter = "+:refs/heads/feature/*"
        }
    }

    features {
        perfmon {
        }
        vcsLabeling {
            vcsRootId = "${DslContext.settingsRoot.id}"
            labelingPattern = "feature-%system.build.number%"
            successfulOnly = true
            branchFilter = "+:feature/*"
        }
    }
})

object IntegrateAndPublish : BuildType({
    name = "Publish Release"

    maxRunningBuildsPerBranch = "*:1"

    params {
        param("build.gameversion", "")
        param("build.version.new", "")
        param("env.GITHUB_LATEST_REF", "")
    }

    vcs {
        root(DslContext.settingsRoot)

        branchFilter = "+:<default>"
    }

    steps {
        python {
            name = "Generate Release Version"
            id = "Generate_Release_Version"
            environment = pipenv {
                arguments = "--python 3.11 pyyaml requests"
            }
            command = file {
                filename = "semver.py"
                scriptArguments = "--api-stable-vs-version"
            }
        }
        dockerCommand {
            id = "DockerCommand"
            commandType = build {
                source = file {
                    path = "Dockerfile"
                }
                platform = DockerCommandStep.ImagePlatform.Linux
                namesAndTags = "registry.dmpsys.in/vintagestory:%env.GITHUB_LATEST_REF%"
            }
        }
    }

    features {
        perfmon {
        }
        vcsLabeling {
            vcsRootId = "${DslContext.settingsRoot.id}"
            labelingPattern = "%build.gameversion%-%build.version.new%"
        }
    }
})

object IntegrateRelease : BuildType({
    name = "Integrate Release"

    params {
        password("system.vcs.auth.token", "credentialsJSON:cd1076b1-4804-4dba-babf-6e3d93e09c68")
        param("build.gameversion", "")
        param("build.version.old", "")
        param("build.docker.version.new", "")
        param("build.version.new", "")
        param("build.docker.tag", "")
    }

    vcs {
        root(DslContext.settingsRoot)
    }

    steps {
        script {
            name = "Setup Python Testing Directory"
            id = "SetupPythonTestingDirectory"
            scriptContent = """
                # Create testing directory
                mkdir -p %env.HOME%/%teamcity.project.id%-VSRconWebClient-%env.BUILD_NUMBER%
                cp -r %teamcity.build.checkoutDir%/vintage_rcon_client/* %env.HOME%/%teamcity.project.id%-VSRconWebClient-%env.BUILD_NUMBER%/.
            """.trimIndent()
        }
        python {
            name = "Run Unit Tests"
            id = "Run_Unit_Tests"
            workingDir = "%env.HOME%/%teamcity.project.id%-VSRconWebClient-%env.BUILD_NUMBER%"
            environment = pipenv {
                arguments = "-r requirements.txt"
            }
            command = pytest {
                isCoverageEnabled = true
            }
        }
        qodana {
            name = "Qodana"
            id = "Qodana"
            workingDir = "%env.HOME%/%teamcity.project.id%-VSRconWebClient-%env.BUILD_NUMBER%"
            reportAsTests = true
            linter = python {
                version = Qodana.PythonVersion.LATEST
            }
            inspectionProfile = default()
            cloudToken = "credentialsJSON:fb6a7bc5-2413-47c0-a09f-087510eac952"
        }
        script {
            name = "Cleanup Testing Directory"
            id = "CleanupTestingDirectory"
            scriptContent = """
                # Delete testing directory
                rm -rf %env.HOME%/%teamcity.project.id%-VSRconWebClient-%env.BUILD_NUMBER%
            """.trimIndent()
        }
        python {
            name = "Integrate Source Branch"
            id = "python_runner"
            enabled = false
            environment = pipenv {
                arguments = "--python 3.11 pyyaml requests"
            }
            command = script {
                content = """
                    import subprocess
                    import os
                    import re
                    import requests
                    import argparse
                    import sys
                    from typing import Tuple, List, Optional, Dict, Any
                    
                    
                    def get_distance_from_main() -> int:
                        ${TQ}Get the number of commits the current branch is ahead of main.$TQ
                        try:
                            result = subprocess.run(
                                ['git', 'rev-list', '--count', 'main..HEAD'],
                                capture_output=True,
                                text=True,
                                check=True
                            )
                            return int(result.stdout.strip())
                        except Exception as e:
                            print(f"Error getting distance from main: {e}")
                            return 0
                    
                    
                    def get_current_git_hash() -> str:
                        ${TQ}Get the shortened git hash of the current HEAD.$TQ
                        try:
                            result = subprocess.run(
                                ['git', 'rev-parse', '--short', 'HEAD'],
                                capture_output=True,
                                text=True,
                                check=True
                            )
                            return result.stdout.strip()
                        except Exception as e:
                            print(f"Error getting git hash: {e}")
                            return 'unknown'
                    
                    
                    def get_prerelease_tags(base_version: str, prerelease_type: str) -> List[str]:
                        $TQ
                        Get all prerelease tags for a given base version and type.
                        For example: get_prerelease_tags("1.0.0", "alpha") returns ["1.0.0-alpha.1", "1.0.0-alpha.2"]
                        $TQ
                        try:
                            result = subprocess.run(
                                ['git', 'tag', '--list', f'{base_version}-{prerelease_type}.*'],
                                capture_output=True,
                                text=True,
                                check=True
                            )
                            tags = [tag.strip() for tag in result.stdout.strip().split('\n') if tag.strip()]
                            return tags
                        except Exception as e:
                            print(f"Error getting prerelease tags: {e}")
                            return []
                    
                    
                    def get_last_version() -> str:
                        ${TQ}Get the last semantic version tag, or return 0.0.0 if none exist.$TQ
                        try:
                            # Get current branch name
                            branch_result = subprocess.run(
                                ['git', 'branch', '--show-current'],
                                capture_output=True,
                                text=True,
                                check=True
                            )
                            current_branch = branch_result.stdout.strip()
                    
                            # Get tags merged into current branch
                            result = subprocess.run(
                                ['git', 'tag', '--merged', current_branch],
                                capture_output=True,
                                text=True,
                                check=True
                            )
                            tags = result.stdout.strip().split('\n')
                            # Filter to only semantic version tags (e.g., 1.0.0)
                            version_tags = [tag for tag in tags if tag and re.match(r'^\d+\.\d+\.\d+${'$'}', tag)]
                    
                            if not version_tags:
                                return '0.0.0'
                    
                            # Sort by version number and return the highest
                            version_tags.sort(key=lambda v: tuple(map(int, v.split('.'))))
                            return version_tags[-1]
                        except Exception as e:
                            print(f"Error getting last version: {e}")
                            return '0.0.0'
                    
                    
                    def get_commits_since_tag(tag: str) -> List[str]:
                        ${TQ}Get commit hashes since the given tag.$TQ
                        try:
                            if tag == '0.0.0':
                                # Get all commits if no tags exist
                                result = subprocess.run(
                                    ['git', 'rev-list', 'HEAD'],
                                    capture_output=True,
                                    text=True,
                                    check=True
                                )
                            else:
                                # Get commits since the tag
                                result = subprocess.run(
                                    ['git', 'rev-list', f'{tag}..HEAD'],
                                    capture_output=True,
                                    text=True,
                                    check=True
                                )
                    
                            commits = [c.strip() for c in result.stdout.strip().split('\n') if c.strip()]
                            return commits
                        except Exception as e:
                            print(f"Error getting commits: {e}")
                            return []
                    
                    
                    def get_commit_message(commit_hash: str) -> Tuple[str, str]:
                        ${TQ}Get commit subject and body.$TQ
                        try:
                            result = subprocess.run(
                                ['git', 'show', '-s', '--format=%%s%%n%%b', commit_hash],
                                capture_output=True,
                                text=True,
                                check=True
                            )
                            lines = result.stdout.split('\n', 1)
                            subject = lines[0] if lines else ''
                            body = lines[1] if len(lines) > 1 else ''
                            return subject, body
                        except Exception as e:
                            print(f"Error getting commit message for {commit_hash}: {e}")
                            return '', ''
                    
                    
                    def determine_bump(commits: List[str]) -> str:
                        $TQ
                        Determine the semantic version bump based on commits.
                        Returns 'major', 'minor', or 'patch'
                        $TQ
                        has_major = False
                        has_minor = False
                    
                        for commit_hash in commits:
                            subject, body = get_commit_message(commit_hash)
                    
                            # Check for BREAKING CHANGE in subject or body
                            if 'BREAKING CHANGE:' in subject or 'BREAKING CHANGE:' in body:
                                has_major = True
                                break
                    
                            # Check for feat! or fix! (exclamation indicates breaking change)
                            if re.match(r'^(feat|fix)!:', subject):
                                has_major = True
                                break
                    
                            # Check for feat: (feature bump)
                            if re.match(r'^feat:', subject):
                                has_minor = True
                    
                            # fix: defaults to patch, so we don't need to explicitly check
                    
                        if has_major:
                            return 'major'
                        elif has_minor:
                            return 'minor'
                        else:
                            # Default to patch if there are commits (even without conventional prefix)
                            return 'patch'
                    
                    
                    def increment_version(version: str, bump: str) -> str:
                        ${TQ}Increment the version based on bump type.$TQ
                        major, minor, patch = map(int, version.split('.'))
                    
                        if bump == 'major':
                            major += 1
                            minor = 0
                            patch = 0
                        elif bump == 'minor':
                            minor += 1
                            patch = 0
                        else:  # patch
                            patch += 1
                    
                        return f'{major}.{minor}.{patch}'
                    
                    
                    def determine_new_version(current_version: str, commits: List[str]) -> Optional[str]:
                        ${TQ}Determine the new version based on current version and commits.$TQ
                        if not commits:
                            print("No new commits since last version")
                            print("Keeping current version:", current_version)
                            return current_version
                    
                        if current_version == '0.0.0':
                            # First version should be 0.0.1
                            print("No previous version found. Setting first version to 0.0.1")
                            return '0.0.1'
                    
                        # Analyze commits and determine bump
                        bump = determine_bump(commits)
                        new_version = increment_version(current_version, bump)
                        print(f"Determined bump type: {bump}")
                        return new_version
                    
                    
                    def determine_prerelease_version(base_version: str, prerelease_type: str) -> str:
                        $TQ
                        Determine the prerelease version with proper increment.
                        If prerelease tags exist for the base version, increment the counter.
                        Otherwise, start at .1
                        $TQ
                        prerelease_tags = get_prerelease_tags(base_version, prerelease_type)
                    
                        if not prerelease_tags:
                            # No existing prerelease tags, start at .1
                            return f"{base_version}-{prerelease_type}.1"
                    
                        # Extract the increment numbers from existing tags
                        increments = []
                        pattern = re.compile(rf'^{re.escape(base_version)}-{re.escape(prerelease_type)}\.(\d+)${'$'}')
                    
                        for tag in prerelease_tags:
                            match = pattern.match(tag)
                            if match:
                                increments.append(int(match.group(1)))
                    
                        if not increments:
                            return f"{base_version}-{prerelease_type}.1"
                    
                        # Get the highest increment and add 1
                        max_increment = max(increments)
                        return f"{base_version}-{prerelease_type}.{max_increment + 1}"
                    
                    
                    def create_git_tag(version: str):
                        ${TQ}Create and push a git tag for the new version.$TQ
                        try:
                            subprocess.run(['git', 'tag', version], check=True)
                            subprocess.run(['git', 'push', 'origin', version], check=True)
                            print(f"✓ Created and pushed git tag: {version}")
                        except subprocess.CalledProcessError as e:
                            print(f"✗ Error creating git tag: {e}")
                            raise
                    
                    
                    class ApiQueryException(Exception):
                        pass
                    
                    
                    def get_api_version(stable):
                        ${TQ}Get the Vintage Story version from the Official HTTP API.$TQ
                        url = "https://api.vintagestory.at/lateststable.txt"
                        if not stable:
                            url = "https://api.vintagestory.at/latestunstable.txt"
                        try:
                            response = requests.get(url)
                            response.raise_for_status()
                            return response.text.strip()
                        except requests.RequestException as e:
                            print(f"Error fetching Vintage Story version from API: {e}")
                            raise ApiQueryException(f"Failed to fetch Vintage Story version from API: {e}")
                    
                    
                    # ===== NEW INTEGRATION FUNCTIONS =====
                    
                    def get_github_token() -> str:
                        ${TQ}Get GitHub token from TeamCity configuration parameter.$TQ
                        token = os.environ.get('GITHUB_TOKEN')
                        if not token:
                            print("✗ Error: GITHUB_TOKEN environment variable not set")
                            print("  Please configure the GITHUB_TOKEN parameter in TeamCity")
                            sys.exit(1)
                        return token
                    
                    
                    def parse_repo_from_git_remote() -> Tuple[str, str]:
                        $TQ
                        Parse GitHub repository owner and name from git remote origin URL.
                        Returns: (owner, repo_name)
                        $TQ
                        try:
                            result = subprocess.run(
                                ['git', 'remote', 'get-url', 'origin'],
                                capture_output=True,
                                text=True,
                                check=True
                            )
                            remote_url = result.stdout.strip()
                            print(f"📡 Detected git remote origin: {remote_url}")
                    
                            # Parse SSH format: git@github.com:owner/repo.git
                            ssh_match = re.match(r'git@github\.com:([^/]+)/(.+?)(?:\.git)?${'$'}', remote_url)
                            if ssh_match:
                                owner, repo = ssh_match.groups()
                                print(f"✓ Parsed repository: {owner}/{repo}")
                                return owner, repo
                    
                            # Parse HTTPS format: https://github.com/owner/repo.git
                            https_match = re.match(r'https://github\.com/([^/]+)/(.+?)(?:\.git)?${'$'}', remote_url)
                            if https_match:
                                owner, repo = https_match.groups()
                                print(f"✓ Parsed repository: {owner}/{repo}")
                                return owner, repo
                    
                            print(f"✗ Error: Could not parse GitHub repository from remote URL: {remote_url}")
                            sys.exit(1)
                        except subprocess.CalledProcessError as e:
                            print(f"✗ Error getting git remote origin: {e}")
                            sys.exit(1)
                    
                    
                    def get_pr_details(owner: str, repo: str, pr_number: int, token: str) -> Dict[str, Any]:
                        $TQ
                        Fetch PR details from GitHub API.
                        $TQ
                        url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
                        headers = {
                            'Authorization': f'token {token}',
                            'Accept': 'application/vnd.github.v3+json'
                        }
                    
                        try:
                            print(f"📥 Fetching PR #{pr_number} details from GitHub API...")
                            response = requests.get(url, headers=headers)
                            response.raise_for_status()
                            pr_data = response.json()
                            print(f"✓ Successfully fetched PR #{pr_number}: {pr_data['title']}")
                            return pr_data
                        except requests.RequestException as e:
                            print(f"✗ Error fetching PR details: {e}")
                            if hasattr(e, 'response') and e.response is not None:
                                print(f"  Response: {e.response.text}")
                            sys.exit(1)
                    
                    
                    def validate_pr_status(pr_data: Dict[str, Any]) -> None:
                        $TQ
                        Validate that the PR exists, is not a draft, and is ready to merge.
                        $TQ
                        print("\n=== Validating PR Status ===")
                    
                        # Check if PR is draft
                        if pr_data.get('draft', False):
                            print(f"✗ Error: PR #{pr_data['number']} is a draft PR")
                            print("  Draft PRs cannot be integrated. Please mark it as ready for review.")
                            sys.exit(1)
                        print("✓ PR is not a draft")
                    
                        # Check if PR is closed
                        if pr_data.get('state') != 'open':
                            print(f"✗ Error: PR #{pr_data['number']} is not open (state: {pr_data.get('state')})")
                            sys.exit(1)
                        print("✓ PR is open")
                    
                    
                    def extract_issue_references(text: str) -> List[int]:
                        $TQ
                        Extract issue references from text using GitHub keywords.
                        Recognizes: close, closes, closed, fix, fixes, fixed, resolve, resolves, resolved
                        $TQ
                        keywords = ['close', 'closes', 'closed', 'fix', 'fixes', 'fixed', 'resolve', 'resolves', 'resolved']
                        pattern = r'\b(?:' + '|'.join(keywords) + r')\s+#(\d+)'
                        matches = re.findall(pattern, text, re.IGNORECASE)
                        return [int(issue_num) for issue_num in matches]
                    
                    
                    def get_linked_issues(owner: str, repo: str, pr_number: int, token: str) -> List[int]:
                        $TQ
                        Get issues linked to the PR via GitHub's timeline API and GraphQL.
                        $TQ
                        url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/timeline"
                        headers = {
                            'Authorization': f'token {token}',
                            'Accept': 'application/vnd.github.mockingbird-preview+json'
                        }
                    
                        try:
                            response = requests.get(url, headers=headers)
                            response.raise_for_status()
                            timeline = response.json()
                    
                            linked_issues = []
                            for event in timeline:
                                if event.get('event') == 'cross-referenced' and event.get('source'):
                                    source = event['source']
                                    if source.get('type') == 'issue':
                                        issue_number = source['issue'].get('number')
                                        if issue_number:
                                            linked_issues.append(issue_number)
                    
                            return linked_issues
                        except requests.RequestException as e:
                            print(f"⚠ Warning: Could not fetch linked issues via timeline API: {e}")
                            return []
                    
                    
                    def validate_issue_association(owner: str, repo: str, pr_data: Dict[str, Any], token: str) -> None:
                        $TQ
                        Validate that the PR is associated with at least one issue.
                        Checks both linked issues and body references.
                        $TQ
                        print("\n=== Validating Issue Association ===")
                    
                        pr_number = pr_data['number']
                        pr_body = pr_data.get('body', '')
                    
                        # Extract issue references from PR body
                        body_references = extract_issue_references(pr_body)
                        print(f"📝 Found {len(body_references)} issue reference(s) in PR body: {body_references}")
                    
                        # Get linked issues via GitHub API
                        linked_issues = get_linked_issues(owner, repo, pr_number, token)
                        print(f"🔗 Found {len(linked_issues)} linked issue(s) via GitHub API: {linked_issues}")
                    
                        # Combine both sources
                        all_issues = set(body_references + linked_issues)
                    
                        if not all_issues:
                            print(f"✗ Error: PR #{pr_number} is not associated with any issues")
                            print("  PRs must reference issues using keywords like 'fixes #123' or be linked to issues")
                            print("  Recognized keywords: close, closes, closed, fix, fixes, fixed, resolve, resolves, resolved")
                            sys.exit(1)
                    
                        print(f"✓ PR is associated with {len(all_issues)} issue(s): {sorted(all_issues)}")
                    
                    
                    def get_required_checks(owner: str, repo: str, branch: str, token: str) -> List[str]:
                        $TQ
                        Get required status checks from branch protection rules.
                        $TQ
                        url = f"https://api.github.com/repos/{owner}/{repo}/branches/{branch}/protection"
                        headers = {
                            'Authorization': f'token {token}',
                            'Accept': 'application/vnd.github.v3+json'
                        }
                    
                        try:
                            response = requests.get(url, headers=headers)
                            if response.status_code == 404:
                                print("⚠ No branch protection rules configured")
                                return []
                    
                            response.raise_for_status()
                            protection = response.json()
                    
                            required_checks = []
                            if 'required_status_checks' in protection and protection['required_status_checks']:
                                contexts = protection['required_status_checks'].get('contexts', [])
                                checks = protection['required_status_checks'].get('checks', [])
                                required_checks.extend(contexts)
                                required_checks.extend([check['context'] for check in checks])
                    
                            return required_checks
                        except requests.RequestException as e:
                            print(f"⚠ Warning: Could not fetch branch protection rules: {e}")
                            return []
                    
                    
                    def get_required_approvals(owner: str, repo: str, branch: str, token: str) -> int:
                        $TQ
                        Get required number of approvals from branch protection rules.
                        Returns 0 if no approvals are required.
                        $TQ
                        url = f"https://api.github.com/repos/{owner}/{repo}/branches/{branch}/protection"
                        headers = {
                            'Authorization': f'token {token}',
                            'Accept': 'application/vnd.github.v3+json'
                        }
                    
                        try:
                            response = requests.get(url, headers=headers)
                            if response.status_code == 404:
                                return 0
                    
                            response.raise_for_status()
                            protection = response.json()
                    
                            if 'required_pull_request_reviews' in protection and protection['required_pull_request_reviews']:
                                return protection['required_pull_request_reviews'].get('required_approving_review_count', 0)
                    
                            return 0
                        except requests.RequestException as e:
                            print(f"⚠ Warning: Could not fetch required approvals: {e}")
                            return 0
                    
                    
                    def validate_checks_and_approvals(owner: str, repo: str, pr_data: Dict[str, Any], token: str) -> None:
                        $TQ
                        Validate that all required checks have passed and PR has required approvals.
                        $TQ
                        print("\n=== Validating Checks and Approvals ===")
                    
                        pr_number = pr_data['number']
                        head_sha = pr_data['head']['sha']
                        base_branch = pr_data['base']['ref']
                    
                        # Get required checks from branch protection
                        required_checks = get_required_checks(owner, repo, base_branch, token)
                        if required_checks:
                            print(f"📋 Required checks: {required_checks}")
                        else:
                            print("📋 No required checks configured")
                    
                        # Get commit status
                        status_url = f"https://api.github.com/repos/{owner}/{repo}/commits/{head_sha}/status"
                        headers = {
                            'Authorization': f'token {token}',
                            'Accept': 'application/vnd.github.v3+json'
                        }
                    
                        try:
                            response = requests.get(status_url, headers=headers)
                            response.raise_for_status()
                            status_data = response.json()
                    
                            state = status_data.get('state', 'pending')
                            print(f"📊 Overall commit status: {state}")
                    
                            if required_checks:
                                # Check individual required checks
                                statuses = status_data.get('statuses', [])
                                status_map = {s['context']: s['state'] for s in statuses}
                    
                                failed_checks = []
                                for check in required_checks:
                                    check_state = status_map.get(check, 'pending')
                                    if check_state != 'success':
                                        failed_checks.append(f"{check} ({check_state})")
                    
                                if failed_checks:
                                    print(f"✗ Error: Required checks have not passed:")
                                    for check in failed_checks:
                                        print(f"  - {check}")
                                    sys.exit(1)
                    
                            # If no specific required checks, verify overall state
                            if state not in ['success', '']:
                                print(f"✗ Error: Commit checks have not passed (state: {state})")
                                sys.exit(1)
                    
                            print("✓ All required checks have passed")
                    
                        except requests.RequestException as e:
                            print(f"⚠ Warning: Could not fetch commit status: {e}")
                    
                        # Check required approvals
                        required_approvals = get_required_approvals(owner, repo, base_branch, token)
                        print(f"👥 Required approvals: {required_approvals}")
                    
                        if required_approvals > 0:
                            reviews_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
                            try:
                                response = requests.get(reviews_url, headers=headers)
                                response.raise_for_status()
                                reviews = response.json()
                    
                                # Count unique approved reviews (latest review per user)
                                user_reviews = {}
                                for review in reviews:
                                    user = review['user']['login']
                                    # Keep only the latest review from each user
                                    if user not in user_reviews or review['submitted_at'] > user_reviews[user]['submitted_at']:
                                        user_reviews[user] = review
                    
                                approved_count = sum(1 for review in user_reviews.values() if review['state'] == 'APPROVED')
                                print(f"✓ Approved reviews: {approved_count}/{required_approvals}")
                    
                                if approved_count < required_approvals:
                                    print(f"✗ Error: PR requires {required_approvals} approval(s) but only has {approved_count}")
                                    sys.exit(1)
                    
                            except requests.RequestException as e:
                                print(f"⚠ Warning: Could not fetch PR reviews: {e}")
                        else:
                            print("✓ No approvals required")
                    
                    
                    def validate_branch_permissions(owner: str, repo: str, branch: str, token: str) -> None:
                        $TQ
                        Validate that we have push permissions to the target branch.
                        $TQ
                        print(f"\n=== Validating Permissions for '{branch}' ===")
                    
                        # Check repository permissions
                        repo_url = f"https://api.github.com/repos/{owner}/{repo}"
                        headers = {
                            'Authorization': f'token {token}',
                            'Accept': 'application/vnd.github.v3+json'
                        }
                    
                        try:
                            response = requests.get(repo_url, headers=headers)
                            response.raise_for_status()
                            repo_data = response.json()
                    
                            permissions = repo_data.get('permissions', {})
                            can_push = permissions.get('push', False)
                            is_admin = permissions.get('admin', False)
                    
                            if not (can_push or is_admin):
                                print(f"✗ Error: No push permission to repository {owner}/{repo}")
                                print("  The configured GITHUB_TOKEN does not have sufficient permissions")
                                sys.exit(1)
                    
                            print(f"✓ Verified push permissions to {owner}/{repo}")
                    
                            # Check branch protection restrictions
                            protection_url = f"https://api.github.com/repos/{owner}/{repo}/branches/{branch}/protection"
                            response = requests.get(protection_url, headers=headers)
                    
                            if response.status_code == 404:
                                print(f"✓ No branch protection on '{branch}'")
                                return
                    
                            if response.status_code == 200:
                                protection = response.json()
                    
                                # Check push restrictions
                                if 'restrictions' in protection and protection['restrictions']:
                                    restrictions = protection['restrictions']
                                    users = restrictions.get('users', [])
                                    teams = restrictions.get('teams', [])
                                    apps = restrictions.get('apps', [])
                    
                                    if users or teams or apps:
                                        print(f"⚠ Branch '{branch}' has push restrictions")
                                        print(f"  Allowed users: {[u['login'] for u in users]}")
                                        print(f"  Allowed teams: {[t['name'] for t in teams]}")
                                        print(f"  Allowed apps: {[a['name'] for a in apps]}")
                                        # Note: We can't easily verify if current token is in restrictions
                                        # The push attempt will fail if not authorized
                    
                                print(f"✓ Branch protection validated for '{branch}'")
                    
                        except requests.RequestException as e:
                            print(f"⚠ Warning: Could not fully validate permissions: {e}")
                    
                    
                    def get_branch_head_sha(branch: str) -> str:
                        $TQ
                        Get the commit SHA of the head of a branch.
                        $TQ
                        try:
                            result = subprocess.run(
                                ['git', 'rev-parse', branch],
                                capture_output=True,
                                text=True,
                                check=True
                            )
                            sha = result.stdout.strip()
                            return sha
                        except subprocess.CalledProcessError as e:
                            print(f"✗ Error getting HEAD SHA for branch '{branch}': {e}")
                            sys.exit(1)
                    
                    
                    def fetch_branches(source_branch: str, target_branch: str) -> None:
                        $TQ
                        Fetch the latest changes for source and target branches.
                        $TQ
                        print(f"\n=== Fetching Latest Changes ===")
                        try:
                            print(f"📥 Fetching origin/{source_branch}...")
                            subprocess.run(
                                ['git', 'fetch', 'origin', source_branch],
                                check=True,
                                capture_output=True
                            )
                            print(f"✓ Fetched origin/{source_branch}")
                    
                            print(f"📥 Fetching origin/{target_branch}...")
                            subprocess.run(
                                ['git', 'fetch', 'origin', target_branch],
                                check=True,
                                capture_output=True
                            )
                            print(f"✓ Fetched origin/{target_branch}")
                    
                        except subprocess.CalledProcessError as e:
                            print(f"✗ Error fetching branches: {e}")
                            if e.stderr:
                                print(f"  {e.stderr.decode()}")
                            sys.exit(1)
                    
                    
                    def compare_branch_heads(source_branch: str, target_branch: str) -> bool:
                        $TQ
                        Compare the HEAD commits of source and target branches.
                        Returns True if they are the same, False otherwise.
                        $TQ
                        print(f"\n=== Comparing Branch HEADs ===")
                    
                        source_sha = get_branch_head_sha(f"origin/{source_branch}")
                        target_sha = get_branch_head_sha(f"origin/{target_branch}")
                    
                        print(f"📍 origin/{source_branch} HEAD: {source_sha}")
                        print(f"📍 origin/{target_branch} HEAD: {target_sha}")
                    
                        if source_sha == target_sha:
                            print(f"✓ Branches are already in sync")
                            return True
                        else:
                            print(f"➜ Branches differ, integration needed")
                            return False
                    
                    
                    def perform_rebase_integration(source_branch: str, target_branch: str) -> None:
                        $TQ
                        Perform rebase integration of source branch into target branch.
                        $TQ
                        print(f"\n=== Performing Rebase Integration ===")
                    
                        try:
                            # Checkout target branch
                            print(f"🔄 Checking out {target_branch}...")
                            subprocess.run(
                                ['git', 'checkout', target_branch],
                                check=True,
                                capture_output=True
                            )
                            print(f"✓ Checked out {target_branch}")
                    
                            # Reset to origin state
                            print(f"🔄 Resetting to origin/{target_branch}...")
                            subprocess.run(
                                ['git', 'reset', '--hard', f'origin/{target_branch}'],
                                check=True,
                                capture_output=True
                            )
                            print(f"✓ Reset to origin/{target_branch}")
                    
                            # Perform rebase
                            print(f"🔄 Rebasing origin/{source_branch} onto {target_branch}...")
                            result = subprocess.run(
                                ['git', 'rebase', f'origin/{source_branch}'],
                                capture_output=True,
                                text=True
                            )
                    
                            if result.returncode != 0:
                                # Rebase failed, abort it
                                print(f"✗ Rebase failed with conflicts")
                                print(f"\nRebase output:")
                                print(result.stdout)
                                if result.stderr:
                                    print(result.stderr)
                    
                                # Abort the rebase
                                print(f"\n🔄 Aborting rebase...")
                                subprocess.run(['git', 'rebase', '--abort'], capture_output=True)
                    
                                print(f"\n✗ Error: Cannot automatically integrate due to rebase conflicts")
                                print(f"  The following conflicts occurred:")
                                print(f"  {result.stdout}")
                                print(f"\n  Manual resolution required:")
                                print(f"  1. Locally checkout {target_branch}")
                                print(f"  2. Run: git rebase origin/{source_branch}")
                                print(f"  3. Resolve conflicts manually")
                                print(f"  4. Run: git rebase --continue")
                                print(f"  5. Push changes")
                                sys.exit(1)
                    
                            print(f"✓ Successfully rebased origin/{source_branch} onto {target_branch}")
                    
                        except subprocess.CalledProcessError as e:
                            print(f"✗ Error during rebase integration: {e}")
                            if e.stderr:
                                print(f"  {e.stderr.decode()}")
                            # Try to abort rebase if it was started
                            subprocess.run(['git', 'rebase', '--abort'], capture_output=True)
                            sys.exit(1)
                    
                    
                    def push_integrated_branch(target_branch: str, version_tag: str) -> None:
                        $TQ
                        Push the integrated branch and version tag to origin.
                        $TQ
                        print(f"\n=== Pushing Integrated Changes ===")
                    
                        try:
                            # Push the rebased branch
                            print(f"📤 Pushing {target_branch} to origin...")
                            result = subprocess.run(
                                ['git', 'push', 'origin', target_branch],
                                capture_output=True,
                                text=True
                            )
                    
                            if result.returncode != 0:
                                print(f"✗ Failed to push {target_branch}")
                                print(f"  {result.stderr}")
                                sys.exit(1)
                    
                            print(f"✓ Successfully pushed {target_branch}")
                    
                            # Create and push the version tag
                            print(f"🏷️  Creating version tag: {version_tag}")
                            subprocess.run(
                                ['git', 'tag', '-a', version_tag, '-m', f'Release {version_tag}'],
                                check=True,
                                capture_output=True
                            )
                    
                            print(f"📤 Pushing tag {version_tag} to origin...")
                            subprocess.run(
                                ['git', 'push', 'origin', version_tag],
                                check=True,
                                capture_output=True
                            )
                    
                            print(f"✓ Successfully created and pushed tag: {version_tag}")
                    
                        except subprocess.CalledProcessError as e:
                            print(f"✗ Error pushing changes: {e}")
                            if e.stderr:
                                print(f"  {e.stderr.decode()}")
                            sys.exit(1)
                    
                    
                    def main():
                        ${TQ}Main integration workflow.$TQ
                        # Setup argument parser
                        parser = argparse.ArgumentParser(
                            description='GitHub PR Integration Script with Semantic Versioning'
                        )
                        parser.add_argument('--name', type=str, required=True,
                                           help='Name of the repository')
                        parser.add_argument('--pr-id', type=int, required=True,
                                           help='Pull Request ID to integrate')
                        parser.add_argument('--target-branch', type=str, default='main',
                                           help='Target branch to integrate into (default: main)')
                        parser.add_argument('--dry-run', action='store_true',
                                            help='Perform a dry run without creating tags or releases')
                        vs_version_group = parser.add_mutually_exclusive_group(required=True)
                        vs_version_group.add_argument('--vs-version', type=str, default=None,
                                            help='Vintage Story version to build for (Default: 1.21.6)')
                        vs_version_group.add_argument('--api-stable-vs-version', action='store_true',
                                            help='Use Vintage Story version from the latest stable API release')
                        vs_version_group.add_argument('--api-unstable-vs-version', action='store_true',
                                            help='Use Vintage Story version from the latest unstable API release')
                    
                        args = parser.parse_args()
                    
                        print("=== GitHub PR Integration Script ===\n")
                    
                        # Check if dry-run mode is active
                        if args.dry_run:
                            print("🔍 DRY-RUN MODE ACTIVE - No tags, pushes, or merges will be performed\n")
                    
                        print(f"Repository Name: {args.name}")
                        print(f"Pull Request: #{args.pr_id}")
                        print(f"Target Branch: {args.target_branch}\n")
                    
                        # Step 1: Get GitHub token
                        token = get_github_token()
                    
                        # Step 2: Parse repository from git remote
                        owner, repo = parse_repo_from_git_remote()
                    
                        # Step 3: Get PR details from GitHub API
                        pr_data = get_pr_details(owner, repo, args.pr_id, token)
                        source_branch = pr_data['head']['ref']
                        target_branch = args.target_branch
                    
                        print(f"📋 Source Branch: {source_branch}")
                        print(f"📋 Target Branch: {target_branch}")
                    
                        # Step 4: Validate PR status (not draft, is open)
                        validate_pr_status(pr_data)
                    
                        # Step 5: Validate issue association
                        validate_issue_association(owner, repo, pr_data, token)
                    
                        # Step 6: Validate checks and approvals
                        validate_checks_and_approvals(owner, repo, pr_data, token)
                    
                        # Step 7: Validate branch permissions
                        validate_branch_permissions(owner, repo, target_branch, token)
                    
                        if args.dry_run:
                            print("\n🔍 DRY-RUN: Skipping git operations")
                            print("✓ All validations passed. Integration would proceed in normal mode.")
                            sys.exit(0)
                    
                        # Step 8: Fetch latest changes
                        fetch_branches(source_branch, target_branch)
                    
                        # Step 9: Compare branch heads
                        if compare_branch_heads(source_branch, target_branch):
                            print(f"\n✓ SUCCESS: {source_branch} is already integrated into {target_branch}")
                            print(f"  No action needed - branches are in sync")
                            sys.exit(0)
                    
                        # Step 10: Get Vintage Story version
                        if not args.vs_version:
                            vs_version = get_api_version(stable=args.api_stable_vs_version)
                        else:
                            vs_version = args.vs_version
                        print(f"\n📦 Vintage Story version: {vs_version}")
                    
                        # Step 11: Determine new version (on target branch context)
                        print(f"\n=== Determining Version ===")
                        current_version = get_last_version()
                        print(f"Current version on {target_branch}: {current_version}")
                    
                        commits = get_commits_since_tag(current_version)
                        print(f"Found {len(commits)} new commits since {current_version}")
                    
                        new_version = determine_new_version(current_version, commits)
                        if new_version is None:
                            print("✗ Cannot determine new version")
                            sys.exit(1)
                    
                        print(f"New version: {new_version}")
                    
                        # Step 12: Perform rebase integration
                        perform_rebase_integration(source_branch, target_branch)
                    
                        # Step 13: Push integrated branch and tags
                        push_integrated_branch(target_branch, new_version)
                    
                        # Step 14: Output version for TeamCity and GitHub Actions
                        print(f"\n=== Build Parameters ===")
                        print(f"##teamcity[setParameter name='build.docker.version.new' value='{new_version}']")
                        print(f"##teamcity[setParameter name='build.docker.tag' value='{vs_version}-{new_version}']")
                        print(f"##teamcity[setParameter name='build.version.new' value='{new_version}']")
                        print(f"##teamcity[setParameter name='build.version.old' value='{current_version}']")
                        print(f"##teamcity[setParameter name='build.gameversion' value='{vs_version}']")
                    
                        print("\n=== ✓ Integration Complete ===")
                        print(f"✓ Successfully integrated PR #{args.pr_id} ({source_branch} → {target_branch})")
                        print(f"✓ Created version tag: {new_version}")
                        print(f"✓ Pushed changes to origin")
                    
                    
                    if __name__ == '__main__':
                        main()
                """.trimIndent()
            }
        }
    }

    failureConditions {
        failOnMetricChange {
            metric = BuildFailureOnMetric.MetricType.TEST_COUNT
            threshold = 20
            units = BuildFailureOnMetric.MetricUnit.PERCENTS
            comparison = BuildFailureOnMetric.MetricComparison.LESS
            compareTo = build {
                buildRule = lastSuccessful()
            }
        }
    }

    features {
        perfmon {
        }
    }
})

object RunTestsAndLinting : BuildType({
    name = "Run Tests and Linting"

    maxRunningBuildsPerBranch = "*:1"
    publishArtifacts = PublishMode.SUCCESSFUL

    outputParams {
        exposeAllParameters = false
    }

    vcs {
        root(HttpsGithubComDarkMatterProductionsVintagestoryRefsHeadsFeaturesWildcard)

        cleanCheckout = true
        branchFilter = """
            +:refs/heads/feature/*
            +:refs/heads/fix/*
        """.trimIndent()
    }

    steps {
        script {
            name = "Setup Python Testing Directory"
            id = "simpleRunner_1"
            scriptContent = """
                # Create testing directory
                mkdir -p %env.HOME%/%teamcity.project.id%-VSRconWebClient-%env.BUILD_NUMBER%
                cp -r %teamcity.build.checkoutDir%/vintage_rcon_client/* %env.HOME%/%teamcity.project.id%-VSRconWebClient-%env.BUILD_NUMBER%/.
            """.trimIndent()
        }
        python {
            name = "Run Unit Tests"
            id = "Run_Unit_Tests_1"
            workingDir = "%env.HOME%/%teamcity.project.id%-VSRconWebClient-%env.BUILD_NUMBER%"
            environment = pipenv {
                arguments = "-r requirements.txt"
            }
            command = pytest {
                isCoverageEnabled = true
            }
        }
        qodana {
            name = "Qodana"
            id = "Qodana_1"
            workingDir = "%env.HOME%/%teamcity.project.id%-VSRconWebClient-%env.BUILD_NUMBER%"
            reportAsTests = true
            linter = python {
                version = Qodana.PythonVersion.LATEST
            }
            inspectionProfile = default()
            cloudToken = "credentialsJSON:fb6a7bc5-2413-47c0-a09f-087510eac952"
        }
        script {
            name = "Cleanup Testing Directory"
            id = "CleanupTestingDirectory_1"
            scriptContent = """
                # Delete testing directory
                rm -rf %env.HOME%/%teamcity.project.id%-VSRconWebClient-%env.BUILD_NUMBER%
            """.trimIndent()
        }
    }

    triggers {
        vcs {
            branchFilter = "+:feature/*"
        }
        vcs {
            branchFilter = "+:refs/heads/fix/*"
        }
    }

    features {
        perfmon {
        }
        vcsLabeling {
            vcsRootId = "${DslContext.settingsRoot.id}"
            labelingPattern = "feature-%system.build.number%"
            successfulOnly = true
            branchFilter = "+:feature/*"
        }
        commitStatusPublisher {
            vcsRootExtId = "${HttpsGithubComDarkMatterProductionsVintagestoryRefsHeadsFeaturesWildcard.id}"
            publisher = github {
                githubUrl = "https://api.github.com"
                authType = storedToken {
                    tokenId = "tc_token_id:CID_5653b11f0397ee3bd028d13e6ac13958:-1:389297e2-c5d6-4093-9b9a-8f70b946b892"
                }
            }
        }
    }
})

object HttpsGithubComDarkMatterProductionsVintagestoryRefsHeadsFeaturesWildcard : GitVcsRoot({
    name = "https://github.com/DarkMatterProductions/vintagestory#refs/heads/features/wildcard"
    url = "https://github.com/DarkMatterProductions/vintagestory"
    branch = "refs/heads/main"
    branchSpec = """
        +:refs/heads/feature/*
        +:refs/heads/fix/*
        +:refs/heads/main
    """.trimIndent()
    userNameStyle = GitVcsRoot.UserNameStyle.FULL
    userForTags = "darkmatter[bot] <noreply@darkmatter-productions.com>"
    authMethod = password {
        userName = "Ralnoc"
        password = "credentialsJSON:a5bba456-f74f-469f-9ba3-25516e69bcc3"
    }
})
