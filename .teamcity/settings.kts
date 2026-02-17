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
        password("env.GITHUB_APP_INSTALLATION_ID", "credentialsJSON:9b36ba2c-234d-4100-aae8-60af89dcfad5")
        param("build.gameversion", "")
        param("build.version.new", "")
        param("build.docker.tag", "")
        text("build.pullrequest.id", "", label = "Pull Request ID#", description = "PR Id to Integrate into main branch", display = ParameterDisplay.PROMPT, allowEmpty = true)
        password("env.GITHUB_APP_ID", "credentialsJSON:824b9fac-e3ae-4f6b-9f4e-881033cca625")
        password("env.GITHUB_APP_PRIVATE_KEY", "credentialsJSON:6ed847ba-6c18-4ab6-877d-33d3e2d1cdbd")
        param("build.version.old", "")
        param("build.docker.version.new", "")
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
        python {
            name = "Integrate PR"
            id = "Integrate_PR"
            environment = pipenv {
                arguments = "--python 3.11 pyyaml PyJWT"
            }
            command = script {
                content = """
                    I'm using Jetbrains TeamCity. It has the VCS Auth Tokens, which are refreshable tokens that can be used in build configurations for granting access to Github. I need to be able to leverage the token id to get access to the auth token, for communicating with Github. 
                    
                    How can this be done within Python? I already have the TeamCuty token id being passed to it through an environment variable.
                    
                    12:31 PM
                    
                    Examined TeamCity token retrieval mechanism and identified clarifying questions needed
                    
                    
                    
                    
                    I'd like to clarify a few things to give you the most relevant solution:
                    
                    Where is your Python script running?
                    Inside a TeamCity build step?
                    On an external server/locally that needs to call TeamCity's API?
                    What do you currently have?
                    Just the token ID (like the name/ID you see in TeamCity UI)?
                    Or do you already have a TeamCity parameter reference (like %teamcity.vcs.auth.token.mytoken%)?
                    Access to TeamCity API:
                    Do you have TeamCity REST API credentials (username/password or personal access token)?
                    The approach differs significantly based on these answers:
                    
                    If running inside TeamCity builds: You can reference tokens directly through parameters
                    If calling from outside: You'd need to use TeamCity's REST API to retrieve token values
                    Which scenario matches your situation?
                    
                    The script is running within a Python runner build step.
                    
                    I have manually placed the token ID into system.vcs.auth.token, which doesn't seem to populate anything automatically, so I mapped it to an environment variable. Of course it does not work.
                    
                    I am not currently passing any TeamCity credentials to the build step. Only the token id.
                    
                    12:34 PM
                    
                    Diagnosed token reference syntax error in TeamCity configuration
                    
                    
                    
                    
                    
                    
                    Ah, I see the issue! You need to use TeamCity's parameter reference syntax to actually retrieve the token value, not just pass the ID.
                    
                    Here's how to fix it:
                    
                    In TeamCity Build Configuration
                    Go to your build configuration → Parameters
                    Add a new Environment Variable:
                    Name: GITHUB_TOKEN (or whatever you prefer)
                    Value: %teamcity.vcs.auth.token.<your-token-id>%
                    For example, if your token ID in TeamCity is github-main-token, you'd use:
                       %teamcity.vcs.auth.token.github-main-token%
                    Make sure it's marked as Password (optional but recommended for security)
                    In Your Python Script
                    Then you can access it normally:
                    
                    python
                    import os
                    from github import Github  # or requests, etc.
                    
                    # Get the actual token value (not the ID)
                    github_token = os.environ.get('GITHUB_TOKEN')
                    
                    if not github_token:
                        raise ValueError("GITHUB_TOKEN environment variable not set")
                    
                    # Use it with GitHub
                    g = Github(github_token)
                    # or with requests
                    headers = {'Authorization': f'token {github_token}'}
                    Key Points
                    system.vcs.auth.token doesn't automatically resolve - you need the % syntax
                    The parameter reference %teamcity.vcs.auth.token.<token-id>% tells TeamCity to substitute the actual token value
                    TeamCity resolves these references before passing to your build step
                    Quick check: What's the exact token ID you see in TeamCity under Administration → VCS Auth Tokens?
                    
                    Am I supposed to use the token id or the token name in the value for the environment variable? The token id is an automated series of hashes and integers. The token name is one I assign.
                    
                    12:36 PM
                    
                    Investigated TeamCity token naming conventions and parameter syntax
                    
                    
                    
                    
                    
                    
                    Use the token name (the one you assigned), not the auto-generated ID.
                    
                    Example
                    If you created a VCS Auth Token with:
                    
                    Name: github-main-token
                    ID: tc_abc123def456... (auto-generated)
                    Your environment variable value should be:
                    
                    %teamcity.vcs.auth.token.github-main-token%
                    Complete Setup
                    TeamCity Parameters:
                    
                    Name: GITHUB_TOKEN
                    Value: %teamcity.vcs.auth.token.your-token-name-here%
                    Type: Environment variable (marked as Password)
                    Python code:
                    
                    python
                    import os
                    
                    github_token = os.environ.get('GITHUB_TOKEN')
                    The token name is what TeamCity uses for the parameter reference syntax - the auto-generated ID is just for internal tracking.
                    
                    What name did you give your VCS Auth Token?
                    
                    
                    import subprocess import os import re import requests import argparse import sys from typing import Tuple, List, Optional, Dict, Any def get_distance_from_main() -> int: ${TQ}Get the number of commits the current branch is ahead of main.$TQ try: result = subprocess.run(
                    
                    pasted
                    
                    Attached is the python script that I am using. Unfortunately it is not working. It results in the error -
                    
                    12:41:21     ✗ Error fetching PR details: 401 Client Error: Unauthorized for url: https://api.github.com/repos/DarkMatterProductions/vintagestory/pulls/60
                    12:41:21       Response: {
                    12:41:21       "message": "Bad credentials",
                    12:41:21       "documentation_url": "https://docs.github.com/rest",
                    12:41:21       "status": "401"
                    12:41:21     }
                    Show more
                    12:44 PM
                    
                    Diagnosed incorrect TeamCity token configuration syntax
                    
                    
                    
                    
                    
                    The issue is in how you're referencing the token. Looking at your code, line 532 is trying to get SYSTEM_VCS_AUTH_TOKEN, but that's not how TeamCity parameter references work.
                    
                    Here's the fix:
                    In TeamCity (Build Configuration → Parameters):
                    Create a new Environment Variable:
                    
                    Name: GITHUB_TOKEN (or keep SYSTEM_VCS_AUTH_TOKEN if you prefer)
                    Value: %teamcity.vcs.auth.token.YOUR-TOKEN-NAME-HERE%
                    Type: Environment variable (env.)
                    Mark as Password: ✓ (recommended)
                    Replace YOUR-TOKEN-NAME-HERE with the actual name you gave your VCS Auth Token in TeamCity (not the auto-generated ID).
                    
                    In Your Python Code (line 530-537):
                    Update the function to match your environment variable name:
                    
                    python
                    def get_github_token() -> str:
                        ${TQ}Get GitHub token from TeamCity configuration parameter.$TQ
                        token = os.environ.get('GITHUB_TOKEN')  # Changed from SYSTEM_VCS_AUTH_TOKEN
                        if not token:
                            print("✗ Error: GITHUB_TOKEN environment variable not set")
                            print("  Please configure the GITHUB_TOKEN parameter in TeamCity with value:")
                            print("  %teamcity.vcs.auth.token.YOUR-TOKEN-NAME%")
                            sys.exit(1)
                        return token
                    Why You're Getting 401:
                    The token value you're passing is likely:
                    
                    The token ID (the hash string) instead of the actual token value
                    Or it's not being resolved at all (empty or contains the literal string instead of the token)
                    The %teamcity.vcs.auth.token.TOKEN_NAME% syntax tells TeamCity to substitute the actual OAuth token value at runtime, which is what GitHub's API needs.
                    
                    What's your VCS Auth Token name in TeamCity? I can give you the exact parameter value to use.
                    
                    You are working from an incorrect premise. The script above is the python code. The environment variable SYSTEM_VCS_AUTH_TOKEN is configured in the build configuration as -
                    
                    Name: env.SYSTEM_VCS_AUTH_TOKEN
                    Kind: Environment Variable
                    Value Type: Password
                    Value: %teamcity.vcs.auth.token.Integrate-and-Release%
                    
                    This matches the described configuration, except I am using SYSTEM_VCS_AUTH_TOKEN instead of GITHUB_TOKEN.
                    
                    12:48 PM
                    
                    Investigated token resolution and identified potential configuration mismatches
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    Ah, I apologize for misunderstanding! Your configuration looks correct. The issue is likely one of these:
                    
                    Debugging Steps:
                    1. Verify the token is actually resolving
                    Add this debug line temporarily after line 537 in your script:
                    
                    python
                    def get_github_token() -> str:
                        ${TQ}Get GitHub token from TeamCity configuration parameter.$TQ
                        token = os.environ.get('SYSTEM_VCS_AUTH_TOKEN')
                        if not token:
                            print("✗ Error: SYSTEM_VCS_AUTH_TOKEN environment variable not set")
                            print("  Please configure the 'system.vcs.auth.token' parameter in TeamCity")
                            sys.exit(1)
                        
                        # Debug: Check if token is resolving
                        print(f"🔍 Token length: {len(token)} characters")
                        print(f"🔍 Token prefix: {token[:7]}..." if len(token) > 7 else f"🔍 Full token: {token}")
                        
                        return token
                    This will show you:
                    
                    If the token is empty
                    If it's still the literal string %teamcity.vcs.auth.token.Integrate-and-Release% (not resolved)
                    If it looks like a valid token (starts with ghp_ or gho_)
                    2. Double-check the exact token name
                    In TeamCity, go to Administration → VCS Auth Tokens and verify:
                    
                    The exact name is Integrate-and-Release (case-sensitive, no extra spaces)
                    The token shows as valid/connected to GitHub
                    3. Verify token permissions
                    The VCS Auth Token needs these GitHub scopes for your script:
                    
                    repo (full repository access)
                    read:org (if accessing organization repos)
                    Check if the token has these scopes in TeamCity's VCS Auth Tokens page.
                    
                    What do you see when you add that debug output?
                    
                    It is valid and the name is correct. I am actually using it in other places on the build configuration. That is how I know it works. 
                    
                    The problem is that it is not actually replacing the value in the environment variable. The debug prints had:  Token prefix: %teamci..., which shows the variable.
                    
                    12:58 PM
                    
                    Diagnosed parameter resolution failure in TeamCity environment variables
                    
                    
                    
                    
                    
                    
                    
                    
                    Ah! The parameter reference isn't being resolved - it's passing the literal string. This is the actual issue.
                    
                    The Problem:
                    TeamCity isn't resolving %teamcity.vcs.auth.token.Integrate-and-Release% when it's inside a Password-type environment variable. This can happen with certain parameter types or contexts.
                    
                    Solution - Try These Approaches:
                    Option 1: Use a System Parameter (Recommended)
                    Instead of env.SYSTEM_VCS_AUTH_TOKEN, create:
                    
                    Name: system.vcs.auth.token
                    Kind: System property
                    Value Type: Password
                    Value: %teamcity.vcs.auth.token.Integrate-and-Release%
                    
                    Then in your Python script, change to:
                    
                    python
                    token = os.environ.get('SYSTEM_VCS_AUTH_TOKEN')
                    TeamCity exposes system.* parameters as environment variables with SYSTEM_ prefix.
                    
                    Option 2: Use Configuration Parameter as Intermediary
                    Create two parameters:
                    
                    Parameter 1:
                    Name: github.token
                    Kind: Configuration parameter
                    Value: %teamcity.vcs.auth.token.Integrate-and-Release%
                    
                    Parameter 2:
                    Name: env.GITHUB_TOKEN
                    Kind: Environment variable
                    Value Type: Password
                    Value: %github.token%
                    
                    Option 3: Reference Directly in Build Step
                    In your Python runner build step, add an environment variable directly:
                    
                    Name: GITHUB_TOKEN
                    Value: %teamcity.vcs.auth.token.Integrate-and-Release%
                    Sometimes build step-level env vars resolve better than configuration-level ones.
                    
                    Try Option 1 first - system parameters typically have the best resolution behavior. What happens with that approach?
                    
                    So far, option 1 has failed with the error -
                    
                    13:03:10     ✗ Error: SYSTEM_VCS_AUTH_TOKEN environment variable not set
                    13:03:10       Please configure the 'system.vcs.auth.token' parameter in TeamCity
                    Option 2 results in the parameter configuration demanding that I set teamcity.vcs.auth.token.Integrate-and-Release
                    
                    1:13 PM
                    
                    Diagnosed naming convention mismatches and explored alternative configuration approaches
                    
                    
                    
                    
                    
                    Ah, I see the issues:
                    
                    Option 1: The parameter name system.vcs.auth.token doesn't automatically become SYSTEM_VCS_AUTH_TOKEN. Let's fix the naming.
                    
                    Option 2: TeamCity thinks it's a circular reference because of how the parameters are structured.
                    
                    Let's Fix Option 1:
                    Change the parameter name to match what your Python code expects:
                    
                    Name: system.vcs.auth.token → system.SYSTEM_VCS_AUTH_TOKEN
                    Kind: System property
                    Value Type: Password
                    Value: %teamcity.vcs.auth.token.Integrate-and-Release%
                    
                    TeamCity will expose system.SYSTEM_VCS_AUTH_TOKEN as the environment variable SYSTEM_VCS_AUTH_TOKEN.
                    
                    OR Try Option 3:
                    In your Python runner build step specifically (not the build configuration parameters):
                    
                    Edit the Python build step
                    Find the Environment variables section in the step
                    Add:
                    Name: SYSTEM_VCS_AUTH_TOKEN
                    Value: %teamcity.vcs.auth.token.Integrate-and-Release%
                    Important Question:
                    You mentioned you're using this token successfully "in other places on the build configuration". How are you referencing it there? (VCS root? Another build step? Script?) If we see how it works there, we can replicate that exact approach.
                    
                    In the other builds steps, they are native runners that can call the auth token as part of TeamCity. 
                    
                    I changed Option 1 to match the 'Fixed' version, but it still failed with -
                    
                    13:22:28     ✗ Error: SYSTEM_VCS_AUTH_TOKEN environment variable not set
                    13:22:28       Please configure the 'system.vcs.auth.token' parameter in TeamCity
                    Option 3 results in the error: teamcity.vcs.auth.token.Integrate-and-Release must have a value (referenced in Build step: Integrate PR) and prevents it from finding a compatible agent.
                    
                    TeamCity is not resolving %teamcity.vcs.auth.token.Integrate-and-Release% automatically to the VCS Auth Tokens anywhere.
                    
                    Show more
                    1:30 PM
                    
                    Diagnosed VCS token exposure limitation and contemplated alternative solutions
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    Ah, now I understand the core issue!
                    
                    The problem: teamcity.vcs.auth.token.* references are special - they only work in specific TeamCity contexts (VCS roots, native runners with built-in GitHub support). They're not regular parameters that can be referenced anywhere with %...% syntax.
                    
                    TeamCity intentionally doesn't expose VCS Auth Tokens to custom scripts through parameter resolution for security reasons.
                    
                    Working Solutions:
                    Option A: Create a Separate GitHub Personal Access Token (Recommended)
                    In GitHub: Create a Personal Access Token with repo scope
                    In TeamCity: Add it as a regular parameter:
                    Name: env.GITHUB_TOKEN
                    Kind: Environment variable
                    Value Type: Password
                    Value: <paste the actual GitHub token>
                    This will work immediately since it's a regular password parameter.
                    
                    Option B: Use TeamCity's REST API (More Complex)
                    If you must use the VCS Auth Token, you'd need to:
                    
                    Give your build access to TeamCity's REST API
                    Use the REST API to fetch the token value at runtime
                    This requires additional TeamCity credentials
                    Option C: Use a Workaround with VCS Checkout
                    Some users configure their VCS root to use the auth token, then extract it from git credentials, but this is fragile and not recommended.
                    
                    My recommendation: Go with Option A. Create a dedicated GitHub PAT for this automation script. The VCS Auth Tokens are designed for TeamCity's internal use, not for exposure to build scripts.
                    
                    Would you like help setting up Option A?
                    
                    No. I can setup Option A. I wanted to leverage the temporary VCS auth tokens, because it is more secure that a static PAT. 
                    
                    Before I set up the static PAT for this setup, are there no options for a dynamic credential process for temporary tokens?
                    
                    1:32 PM
                    
                    Examined dynamic credential alternatives to static PATs
                    
                    
                    
                    
                    
                    Good question! There are a few options for dynamic/temporary credentials:
                    
                    Option 1: GitHub App with Installation Tokens (Best Alternative)
                    Instead of a PAT, use a GitHub App:
                    
                    Create a GitHub App in your org/repo settings
                    Install it on your repository
                    In your Python script, generate short-lived installation tokens (valid for 1 hour):
                    python
                    import jwt
                    import time
                    import requests
                    
                    def get_github_app_token(app_id: str, private_key: str, installation_id: str) -> str:
                        ${TQ}Generate a short-lived GitHub App installation token (1 hour validity).$TQ
                        
                        # Create JWT
                        payload = {
                            'iat': int(time.time()),
                            'exp': int(time.time()) + 600,  # 10 min
                            'iss': app_id
                        }
                        jwt_token = jwt.encode(payload, private_key, algorithm='RS256')
                        
                        # Get installation token
                        headers = {
                            'Authorization': f'Bearer {jwt_token}',
                            'Accept': 'application/vnd.github.v3+json'
                        }
                        response = requests.post(
                            f'https://api.github.com/app/installations/{installation_id}/access_tokens',
                            headers=headers
                        )
                        return response.json()['token']
                    Store in TeamCity:
                    
                    env.GITHUB_APP_ID
                    env.GITHUB_APP_PRIVATE_KEY (password)
                    env.GITHUB_APP_INSTALLATION_ID
                    Advantages:
                    
                    Tokens expire in 1 hour
                    Fine-grained permissions
                    Better audit trail
                    Option 2: TeamCity REST API (Hacky)
                    Access the VCS Auth Token via TeamCity's API from within the build:
                    
                    python
                    def get_vcs_token_via_api():
                        tc_url = os.environ.get('TEAMCITY_URL')  # Automatically available
                        tc_token = os.environ.get('TEAMCITY_API_TOKEN')  # You'd need to add this
                        
                        # Call TeamCity API to get VCS root details
                        # This is complex and requires knowing VCS root IDs
                    Downsides: Requires exposing TeamCity API credentials, complex setup
                    
                    Option 3: OIDC Token Exchange (If Available)
                    Check if your TeamCity version supports OIDC - some newer versions might allow workload identity federation with GitHub.
                    
                    My Recommendation: GitHub App (Option 1) is the industry-standard approach for temporary credentials. It's what GitHub Actions uses internally, and it's more secure than static PATs while being actually accessible from scripts.
                    
                    Would you like help setting up the GitHub App approach?
                    
                    I am absolutely on board with using Option 1. I already have the Github App integration in place for TeamCity. That is what Team City is using for generating the VCS Auth Tokens. 
                    
                    Is there a way we can also use the Github App permissions within the script for handling local git commands for merging, rebasing, tagging and pushing branches from the local checkout to Github?
                    
                    1:35 PM
                    
                    Architected solution leveraging existing GitHub App credentials for local git operations
                    
                    
                    
                    
                    
                    Absolutely! Since TeamCity is already using the GitHub App, you can leverage the same App credentials in your script.
                    
                    Here's how to set it up:
                    1. Extract GitHub App Credentials from TeamCity
                    You need to add these as TeamCity parameters (they're likely already configured somewhere in TeamCity, you just need to expose them):
                    
                    Build Configuration → Parameters:
                    
                    env.GITHUB_APP_ID = <your-app-id>
                    env.GITHUB_APP_INSTALLATION_ID = <your-installation-id>
                    env.GITHUB_APP_PRIVATE_KEY = <your-private-key-pem> (Password type)
                    To find these values:
                    
                    App ID: GitHub → Settings → Developer settings → GitHub Apps → Your App
                    Installation ID: Install the app, then check the URL or use API
                    Private Key: Generate/download from GitHub App settings
                    2. Update Your Python Script
                    Replace the get_github_token() function with this:
                    
                    python
                    import jwt
                    import time
                    
                    def get_github_app_installation_token() -> str:
                        $TQ
                        Generate a GitHub App installation token (valid for 1 hour).
                        Uses GitHub App credentials from TeamCity environment variables.
                        $TQ
                        app_id = os.environ.get('GITHUB_APP_ID')
                        private_key = os.environ.get('GITHUB_APP_PRIVATE_KEY')
                        installation_id = os.environ.get('GITHUB_APP_INSTALLATION_ID')
                        
                        if not all([app_id, private_key, installation_id]):
                            print("✗ Error: GitHub App credentials not configured")
                            print("  Required environment variables:")
                            print("  - GITHUB_APP_ID")
                            print("  - GITHUB_APP_PRIVATE_KEY")
                            print("  - GITHUB_APP_INSTALLATION_ID")
                            sys.exit(1)
                        
                        try:
                            # Create JWT for GitHub App authentication
                            now = int(time.time())
                            payload = {
                                'iat': now,
                                'exp': now + 600,  # JWT expires in 10 minutes
                                'iss': app_id
                            }
                            
                            jwt_token = jwt.encode(payload, private_key, algorithm='RS256')
                            
                            # Exchange JWT for installation token
                            headers = {
                                'Authorization': f'Bearer {jwt_token}',
                                'Accept': 'application/vnd.github.v3+json'
                            }
                            
                            print(f"🔐 Requesting GitHub App installation token...")
                            response = requests.post(
                                f'https://api.github.com/app/installations/{installation_id}/access_tokens',
                                headers=headers
                            )
                            response.raise_for_status()
                            
                            token_data = response.json()
                            token = token_data['token']
                            expires_at = token_data['expires_at']
                            
                            print(f"✓ Generated installation token (expires: {expires_at})")
                            return token
                            
                        except Exception as e:
                            print(f"✗ Error generating GitHub App token: {e}")
                            sys.exit(1)
                    3. Configure Git to Use the Token
                    Add this function to configure git with the installation token:
                    
                    python
                    def configure_git_credentials(token: str, owner: str, repo: str) -> None:
                        $TQ
                        Configure git to use the GitHub App installation token for authentication.
                        $TQ
                        print(f"\n=== Configuring Git Credentials ===")
                        
                        try:
                            # Set up git credential helper with the token
                            # Option 1: Update the remote URL to include token
                            remote_url = f'https://x-access-token:{token}@github.com/{owner}/{repo}.git'
                            
                            subprocess.run(
                                ['git', 'remote', 'set-url', 'origin', remote_url],
                                check=True,
                                capture_output=True
                            )
                            print(f"✓ Configured git remote with installation token")
                            
                            # Configure git user for commits/tags (use GitHub App bot)
                            subprocess.run(
                                ['git', 'config', 'user.name', 'github-actions[bot]'],
                                check=True,
                                capture_output=True
                            )
                            subprocess.run(
                                ['git', 'config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com'],
                                check=True,
                                capture_output=True
                            )
                            print(f"✓ Configured git user identity")
                            
                        except subprocess.CalledProcessError as e:
                            print(f"✗ Error configuring git credentials: {e}")
                            sys.exit(1)
                    4. Update Your main() Function
                    Replace line 805 with:
                    
                    python
                    def main():
                        # ... existing code ...
                        
                        # Step 1: Get GitHub App installation token
                        token = get_github_app_installation_token()
                        
                        # Step 2: Parse repository from git remote
                        owner, repo = parse_repo_from_git_remote()
                        
                        # Step 3: Configure git to use the token
                        configure_git_credentials(token, owner, repo)
                        
                        # ... rest of your existing code ...
                    5. Add Required Dependency
                    Add to your requirements or install:
                    
                    bash
                    pip install PyJWT cryptography
                    Benefits:
                    ✅ Temporary tokens (1 hour expiry)
                    ✅ No static PATs needed
                    ✅ Same permissions TeamCity already has
                    ✅ Works with all git operations (fetch, push, tag)
                    ✅ Audit trail through GitHub App
                    
                    Finding Your Installation ID:
                    If you don't know your installation ID:
                    
                    python
                    def get_installation_id(app_id: str, private_key: str, owner: str) -> str:
                        ${TQ}Find installation ID for a given org/user.$TQ
                        now = int(time.time())
                        payload = {'iat': now, 'exp': now + 600, 'iss': app_id}
                        jwt_token = jwt.encode(payload, private_key, algorithm='RS256')
                        
                        headers = {
                            'Authorization': f'Bearer {jwt_token}',
                            'Accept': 'application/vnd.github.v3+json'
                        }
                        
                        response = requests.get(
                            f'https://api.github.com/app/installations',
                            headers=headers
                        )
                        
                        for installation in response.json():
                            if installation['account']['login'] == owner:
                                return str(installation['id'])
                        
                        raise Exception(f"No installation found for {owner}")
                    Would you like help extracting the GitHub App credentials from your existing TeamCity setup?
                    
                    I'm not clear where I get GITHUB_APP_INSTALLATION_ID. Is that somewhere in TeamCity? Or is it in Github?
                    
                    1:43 PM
                    
                    Clarified GitHub App installation ID origins and retrieval methods
                    
                    
                    
                    
                    The GITHUB_APP_INSTALLATION_ID is in GitHub, but there are a few ways to get it:
                    
                    Method 1: From GitHub URL (Easiest)
                    Go to your GitHub organization settings (or user settings if personal)
                    Navigate to: Settings → GitHub Apps → (Your App Name)
                    Or go to: Settings → Installations → Configure (next to your app)
                    Look at the URL - it will be something like:
                       https://github.com/settings/installations/12345678
                    The number at the end (12345678) is your Installation ID
                    
                    Method 2: From TeamCity Configuration (If Exposed)
                    Check if TeamCity stores it:
                    
                    Go to TeamCity → Administration → Connections
                    Find your GitHub App connection
                    Look for any "Installation ID" field (TeamCity might display it, but it's not guaranteed)
                    Method 3: Use the API to Find It (Programmatic)
                    Add this helper function to your script to auto-discover it:
                    
                    python
                    def get_github_app_installation_id(app_id: str, private_key: str, owner: str) -> str:
                        $TQ
                        Find the installation ID for a GitHub App installed on an organization/user.
                        
                        Args:
                            app_id: GitHub App ID
                            private_key: GitHub App private key (PEM format)
                            owner: GitHub organization or user name
                        
                        Returns:
                            Installation ID as a string
                        $TQ
                        import jwt
                        import time
                        
                        # Create JWT
                        now = int(time.time())
                        payload = {
                            'iat': now,
                            'exp': now + 600,
                            'iss': app_id
                        }
                        
                        jwt_token = jwt.encode(payload, private_key, algorithm='RS256')
                        
                        # List all installations for this app
                        headers = {
                            'Authorization': f'Bearer {jwt_token}',
                            'Accept': 'application/vnd.github.v3+json'
                        }
                        
                        print(f"🔍 Looking up installation ID for {owner}...")
                        response = requests.get(
                            'https://api.github.com/app/installations',
                            headers=headers
                        )
                        response.raise_for_status()
                        
                        installations = response.json()
                        
                        for installation in installations:
                            account = installation.get('account', {})
                            if account.get('login') == owner:
                                installation_id = str(installation['id'])
                                print(f"✓ Found installation ID: {installation_id}")
                                return installation_id
                        
                        print(f"✗ No installation found for {owner}")
                        print(f"Available installations:")
                        for inst in installations:
                            print(f"  - {inst['account']['login']} (ID: {inst['id']})")
                        sys.exit(1)
                    Then update your token function:
                    
                    python
                    def get_github_app_installation_token(owner: str) -> str:
                        ${TQ}Generate a GitHub App installation token.$TQ
                        app_id = os.environ.get('GITHUB_APP_ID')
                        private_key = os.environ.get('GITHUB_APP_PRIVATE_KEY')
                        installation_id = os.environ.get('GITHUB_APP_INSTALLATION_ID')  # Optional now
                        
                        if not all([app_id, private_key]):
                            print("✗ Error: GitHub App credentials not configured")
                            sys.exit(1)
                        
                        # Auto-discover installation ID if not provided
                        if not installation_id:
                            print("⚠ GITHUB_APP_INSTALLATION_ID not set, auto-discovering...")
                            installation_id = get_github_app_installation_id(app_id, private_key, owner)
                        
                        # ... rest of token generation ...
                    Recommended Approach:
                    Use Method 1 to manually find the Installation ID from GitHub UI
                    Add it to TeamCity as a parameter: env.GITHUB_APP_INSTALLATION_ID
                    Or use Method 3 to auto-discover it at runtime (slightly slower but more flexible)
                    Which method would you prefer?
                    
                    
                    import subprocess import os import re import requests import argparse import sys from typing import Tuple, List, Optional, Dict, Any def get_distance_from_main() -> int: ${TQ}Get the number of commits the current branch is ahead of main.$TQ try: result = subprocess.run(
                    
                    pasted
                    
                    Ok. got it. 
                    
                    Can you please replace get_github_token() with the code for using these new environment variables. Please make sure that it will work with the local git cli commands that run in subprocess as well.
                    
                    1:47 PM
                    
                    Architected GitHub App authentication with git CLI subprocess integration
                    
                    
                    
                    Here's the updated code to replace the get_github_token() function and add git credential configuration:
                    
                    python
                    import jwt
                    import time
                    
                    def get_github_app_installation_token() -> str:
                        $TQ
                        Generate a GitHub App installation token (valid for 1 hour).
                        Uses GitHub App credentials from TeamCity environment variables.
                        $TQ
                        app_id = os.environ.get('GITHUB_APP_ID')
                        private_key = os.environ.get('GITHUB_APP_PRIVATE_KEY')
                        installation_id = os.environ.get('GITHUB_APP_INSTALLATION_ID')
                        
                        if not all([app_id, private_key, installation_id]):
                            print("✗ Error: GitHub App credentials not configured")
                            print("  Required environment variables:")
                            print("  - GITHUB_APP_ID")
                            print("  - GITHUB_APP_PRIVATE_KEY")
                            print("  - GITHUB_APP_INSTALLATION_ID")
                            sys.exit(1)
                        
                        try:
                            # Create JWT for GitHub App authentication
                            now = int(time.time())
                            payload = {
                                'iat': now,
                                'exp': now + 600,  # JWT expires in 10 minutes
                                'iss': app_id
                            }
                            
                            print(f"🔐 Generating GitHub App JWT...")
                            jwt_token = jwt.encode(payload, private_key, algorithm='RS256')
                            
                            # Exchange JWT for installation token
                            headers = {
                                'Authorization': f'Bearer {jwt_token}',
                                'Accept': 'application/vnd.github.v3+json'
                            }
                            
                            print(f"🔐 Requesting GitHub App installation token...")
                            response = requests.post(
                                f'https://api.github.com/app/installations/{installation_id}/access_tokens',
                                headers=headers
                            )
                            response.raise_for_status()
                            
                            token_data = response.json()
                            token = token_data['token']
                            expires_at = token_data['expires_at']
                            
                            print(f"✓ Generated installation token (expires: {expires_at})")
                            return token
                            
                        except requests.RequestException as e:
                            print(f"✗ Error generating GitHub App token: {e}")
                            if hasattr(e, 'response') and e.response is not None:
                                print(f"  Response: {e.response.text}")
                            sys.exit(1)
                        except Exception as e:
                            print(f"✗ Error generating GitHub App token: {e}")
                            sys.exit(1)
                    
                    
                    def configure_git_credentials(token: str, owner: str, repo: str) -> None:
                        $TQ
                        Configure git to use the GitHub App installation token for authentication.
                        This allows git push, fetch, and other operations to work with the temporary token.
                        $TQ
                        print(f"\n=== Configuring Git Credentials ===")
                        
                        try:
                            # Update the remote URL to include the token
                            # Format: https://x-access-token:TOKEN@github.com/owner/repo.git
                            remote_url = f'https://x-access-token:{token}@github.com/{owner}/{repo}.git'
                            
                            subprocess.run(
                                ['git', 'remote', 'set-url', 'origin', remote_url],
                                check=True,
                                capture_output=True
                            )
                            print(f"✓ Configured git remote with installation token")
                            
                            # Configure git user for commits/tags
                            # Using GitHub Actions bot identity
                            subprocess.run(
                                ['git', 'config', 'user.name', 'github-actions[bot]'],
                                check=True,
                                capture_output=True
                            )
                            subprocess.run(
                                ['git', 'config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com'],
                                check=True,
                                capture_output=True
                            )
                            print(f"✓ Configured git user identity")
                            
                        except subprocess.CalledProcessError as e:
                            print(f"✗ Error configuring git credentials: {e}")
                            if e.stderr:
                                print(f"  {e.stderr.decode()}")
                            sys.exit(1)
                    And update the main() function - replace lines 805-816 with:
                    
                    python
                    def main():
                        ${TQ}Main integration workflow.$TQ
                        # Setup argument parser
                        parser = argparse.ArgumentParser(
                            description='GitHub PR Integration Script with Semantic Versioning'
                        )
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
                    
                        print(f"Pull Request: #{args.pr_id}")
                        print(f"Target Branch: {args.target_branch}\n")
                    
                        # Step 1: Generate GitHub App installation token
                        token = get_github_app_installation_token()
                    
                        # Step 2: Parse repository from git remote
                        owner, repo = parse_repo_from_git_remote()
                    
                        # Step 3: Configure git credentials with the token
                        configure_git_credentials(token, owner, repo)
                    
                        # Step 4: Get PR details from GitHub API
                        pr_data = get_pr_details(owner, repo, args.pr_id, token)
                        source_branch = pr_data['head']['ref']
                        target_branch = args.target_branch
                    
                        print(f"📋 Source Branch: {source_branch}")
                        print(f"📋 Target Branch: {target_branch}")
                    
                        # Continue with rest of the function...
                    Also add this to your imports at the top:
                    
                    python
                    import jwt
                    import time
                    And add to your requirements.txt or install:
                    
                    bash
                    pip install PyJWT cryptography
                    Summary of changes:
                    
                    ✅ Replaced get_github_token() with get_github_app_installation_token()
                    ✅ Added configure_git_credentials() to update git remote URL with token
                    ✅ Token is configured for ALL git CLI commands (fetch, push, rebase, tag, etc.)
                    ✅ Uses temporary 1-hour tokens from GitHub App
                    ✅ Works with your existing subprocess git commands
                    The token will now be embedded in the git remote URL, so all your existing subprocess.run(['git', ...]) commands will automatically authenticate!
                    
                    Please update the script to contain those sections. Make sure you do not change any other code, except what is required to make that change work.
                    
                    1:48 PM
                    
                    Verified file creation and catalogued modifications
                    
                    
                    
                    
                    
                    
                    Perfect! I've updated your script with the GitHub App authentication. Here's what changed:
                    
                    Changes Made:
                    Added imports (lines 7-8):
                    import jwt
                    import time
                    Replaced get_github_token() with get_github_app_installation_token() (lines 264-316):
                    Reads GITHUB_APP_ID, GITHUB_APP_PRIVATE_KEY, GITHUB_APP_INSTALLATION_ID from environment
                    Creates a JWT token
                    Exchanges it for a 1-hour GitHub App installation token
                    Added configure_git_credentials() function (lines 319-353):
                    Updates git remote URL with the token: https://x-access-token:TOKEN@github.com/owner/repo.git
                    Configures git user identity for commits/tags
                    This ensures all git subprocess commands (fetch, push, rebase, tag) authenticate automatically
                    Updated main() function:
                    Step 1: Changed to call get_github_app_installation_token()
                    Step 3: Added call to configure_git_credentials(token, owner, repo)
                    Renumbered subsequent steps (4-15)
                    What You Need to Do in TeamCity:
                    Add these environment variables to your build configuration:
                    
                    env.GITHUB_APP_ID = <your-app-id>
                    env.GITHUB_APP_INSTALLATION_ID = <installation-id>
                    env.GITHUB_APP_PRIVATE_KEY = <private-key-pem> (mark as Password)
                    Install Required Python Packages:
                    bash
                    pip install PyJWT cryptography requests
                    The script will now use temporary 1-hour tokens from your GitHub App, and all git operations will authenticate automatically!
                    
                    Integrate pr
                    PY 
                    How does this use GITHUB_APP_PRIVATE_KEY to allow the git cli tool to communicate with Github?
                    
                    2:32 PM
                    
                    Traced private key's indirect role in git authentication flow
                    
                    
                    
                    
                    Great question! The GITHUB_APP_PRIVATE_KEY doesn't directly communicate with GitHub for git operations. Here's the flow:
                    
                    Authentication Flow:
                    GITHUB_APP_PRIVATE_KEY (PEM format)
                             ↓
                        Creates JWT Token (signed with private key)
                             ↓
                        Sends JWT to GitHub API
                             ↓
                        GitHub returns Installation Token (1-hour lived access token)
                             ↓
                        Installation Token embedded in git remote URL
                             ↓
                        Git CLI uses the Installation Token for all operations
                    Specifically in the code:
                    Step 1: Private Key → JWT Token
                    python
                    # In get_github_app_installation_token()
                    jwt_token = jwt.encode(payload, private_key, algorithm='RS256')
                    # This creates a signed JWT that proves we own the GitHub App
                    Step 2: JWT → Installation Token
                    python
                    # Exchange JWT for installation token via GitHub API
                    response = requests.post(
                        f'https://api.github.com/app/installations/{installation_id}/access_tokens',
                        headers={'Authorization': f'Bearer {jwt_token}'}
                    )
                    token = response.json()['token']  # This is what git will use
                    Step 3: Installation Token → Git Remote URL
                    python
                    # In configure_git_credentials()
                    remote_url = f'https://x-access-token:{token}@github.com/{owner}/{repo}.git'
                    subprocess.run(['git', 'remote', 'set-url', 'origin', remote_url])
                    ```
                    
                    ## What Git Actually Sees:
                    
                    When git runs commands like `git push origin main`, it sees the remote URL as:
                    ```
                    https://x-access-token:ghs_abc123xyz...@github.com/owner/repo.git
                    The ghs_abc123xyz... part is the installation token (not the private key). Git sends this token in HTTP Basic Auth to GitHub with each request.
                    
                    Summary:
                    Private Key: Only used by Python to create the JWT
                    JWT: Only used to request the installation token from GitHub's API
                    Installation Token: This is what git CLI actually uses for authentication
                    Git: Never sees the private key, only the installation token in the URL
                    The private key stays in Python memory and is never exposed to git commands. Does that clarify the flow?
                    
                    The script fails with 
                    
                    14:43:42     🔐 Generating GitHub App JWT...
                    14:43:42     ✗ Error generating GitHub App token: module 'jwt' has no attribute 'encode'
                    2:45 PM
                    
                    Diagnosed package conflict and formulated installation solution
                    
                    
                    
                    
                    
                    The issue is that you have the wrong jwt package installed. There are two different packages:
                    
                    jwt (wrong one - doesn't have encode)
                    PyJWT (correct one - has encode)
                    Fix:
                    Option 1: Install the correct package
                    
                    In your TeamCity build step (before running the Python script), add:
                    
                    bash
                    pip uninstall -y jwt
                    pip install PyJWT cryptography
                    Option 2: Update the import to be explicit
                    
                    Change the import at the top of the script:
                    
                    python
                    # Instead of: import jwt
                    import jwt as pyjwt  # or
                    from jwt import encode as jwt_encode
                    Then update the encode call:
                    
                    python
                    jwt_token = pyjwt.encode(payload, private_key, algorithm='RS256')
                    # or
                    jwt_token = jwt_encode(payload, private_key, algorithm='RS256')
                    Option 3: Add a check in the script
                    
                    I can update the script to detect and give a better error message:
                    
                    python
                    try:
                        import jwt
                        # Verify it's PyJWT, not the jwt package
                        if not hasattr(jwt, 'encode'):
                            print("✗ Error: Wrong 'jwt' package installed")
                            print("  Please run: pip uninstall jwt && pip install PyJWT")
                            sys.exit(1)
                    except ImportError:
                        print("✗ Error: PyJWT not installed")
                        print("  Please run: pip install PyJWT cryptography")
                        sys.exit(1)
                    I recommend Option 1 - just make sure PyJWT is installed instead of jwt.
                    
                    Would you like me to update the script with Option 3 to give a better error message if the wrong package is detected?
                    
                    installing pyjwt fixed that issue. The only remaining issue is that I am getting the error -
                    
                        if not all_issues:
                            print(f"✗ Error: PR #{pr_number} is not associated with any issues")
                            print("  PRs must reference issues using keywords like 'fixes #123' or be linked to issues")
                            print("  Recognized keywords: close, closes, closed, fix, fixes, fixed, resolve, resolves, resolved")
                            sys.exit(1)
                    which means that it is scanning the PR body, not not checking of the PR is linked to issues.
                    
                    Show more
                    3:07 PM
                    
                    Investigated API limitations and pivoted toward GraphQL solution
                    
                    
                    
                    
                    
                    The timeline API approach isn't reliably detecting linked issues. Let's use GitHub's GraphQL API instead, which has better support for this.
                    
                    Here's the updated get_linked_issues() function:
                    
                    
                    Prepared to clarify the issue detection mechanism discrepancy
                    
                    
                    Perfect! I've updated the get_linked_issues() function to use GitHub's GraphQL API, which is much more reliable for detecting linked issues.
                    
                    What Changed:
                    The new function uses GraphQL to query closingIssuesReferences, which GitHub automatically tracks when:
                    
                    A PR body/comment contains keywords like "fixes #123", "closes #456"
                    Issues are manually linked to the PR through GitHub's UI
                    Why GraphQL is Better:
                    More reliable: GitHub's GraphQL API explicitly tracks closing references
                    Comprehensive: Captures both keyword references AND manually linked issues
                    Standardized: Uses GitHub's built-in linking system
                    The GraphQL Query:
                    graphql
                    query {
                      repository(owner: "owner", name: "repo") {
                        pullRequest(number: 60) {
                          closingIssuesReferences(first: 10) {
                            nodes {
                              number
                            }
                          }
                        }
                      }
                    }
                    This directly asks GitHub "what issues will this PR close?"
                    
                    Testing:
                    Try running the script again. It should now properly detect:
                    
                    Issues referenced with keywords in PR body (fixes #123, closes #456, etc.)
                    Issues manually linked through GitHub's "Development" sidebar
                    Issues linked in PR comments
                    If it still doesn't find linked issues, you may need to either:
                    
                    Add a keyword reference to the PR body (e.g., "Fixes #123")
                    Manually link an issue via GitHub's UI
                    Or we can make this validation optional if your workflow doesn't require it
                    Does it work now?
                    
                    Integrate pr
                    PY 
                    
                    
                    
                    
                    Claude is AI and can make mistakes. Please double-check responses.
                    Integrate pr · PY
                    Copy
                    
                    import subprocess
                    import os
                    import re
                    import requests
                    import argparse
                    import sys
                    import jwt
                    import time
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
                    
                    
                    def get_vs_version(stable):
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
                    
                    def get_github_app_installation_token() -> str:
                        $TQ
                        Generate a GitHub App installation token (valid for 1 hour).
                        Uses GitHub App credentials from TeamCity environment variables.
                        $TQ
                        app_id = os.environ.get('GITHUB_APP_ID')
                        private_key = os.environ.get('GITHUB_APP_PRIVATE_KEY')
                        installation_id = os.environ.get('GITHUB_APP_INSTALLATION_ID')
                        
                        if not all([app_id, private_key, installation_id]):
                            print("✗ Error: GitHub App credentials not configured")
                            print("  Required environment variables:")
                            print("  - GITHUB_APP_ID")
                            print("  - GITHUB_APP_PRIVATE_KEY")
                            print("  - GITHUB_APP_INSTALLATION_ID")
                            sys.exit(1)
                        
                        try:
                            # Create JWT for GitHub App authentication
                            now = int(time.time())
                            payload = {
                                'iat': now,
                                'exp': now + 600,  # JWT expires in 10 minutes
                                'iss': app_id
                            }
                            
                            print(f"🔐 Generating GitHub App JWT...")
                            jwt_token = jwt.encode(payload, private_key, algorithm='RS256')
                            
                            # Exchange JWT for installation token
                            headers = {
                                'Authorization': f'Bearer {jwt_token}',
                                'Accept': 'application/vnd.github.v3+json'
                            }
                            
                            print(f"🔐 Requesting GitHub App installation token...")
                            response = requests.post(
                                f'https://api.github.com/app/installations/{installation_id}/access_tokens',
                                headers=headers
                            )
                            response.raise_for_status()
                            
                            token_data = response.json()
                            token = token_data['token']
                            expires_at = token_data['expires_at']
                            
                            print(f"✓ Generated installation token (expires: {expires_at})")
                            return token
                            
                        except requests.RequestException as e:
                            print(f"✗ Error generating GitHub App token: {e}")
                            if hasattr(e, 'response') and e.response is not None:
                                print(f"  Response: {e.response.text}")
                            sys.exit(1)
                        except Exception as e:
                            print(f"✗ Error generating GitHub App token: {e}")
                            sys.exit(1)
                    
                    
                    def configure_git_credentials(token: str, owner: str, repo: str) -> None:
                        $TQ
                        Configure git to use the GitHub App installation token for authentication.
                        This allows git push, fetch, and other operations to work with the temporary token.
                        $TQ
                        print(f"\n=== Configuring Git Credentials ===")
                        
                        try:
                            # Update the remote URL to include the token
                            # Format: https://x-access-token:TOKEN@github.com/owner/repo.git
                            remote_url = f'https://x-access-token:{token}@github.com/{owner}/{repo}.git'
                            
                            subprocess.run(
                                ['git', 'remote', 'set-url', 'origin', remote_url],
                                check=True,
                                capture_output=True
                            )
                            print(f"✓ Configured git remote with installation token")
                            
                            # Configure git user for commits/tags
                            # Using GitHub Actions bot identity
                            subprocess.run(
                                ['git', 'config', 'user.name', 'github-actions[bot]'],
                                check=True,
                                capture_output=True
                            )
                            subprocess.run(
                                ['git', 'config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com'],
                                check=True,
                                capture_output=True
                            )
                            print(f"✓ Configured git user identity")
                            
                        except subprocess.CalledProcessError as e:
                            print(f"✗ Error configuring git credentials: {e}")
                            if e.stderr:
                                print(f"  {e.stderr.decode()}")
                            sys.exit(1)
                    
                    
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
                        Get issues linked to the PR via GitHub's GraphQL API.
                        $TQ
                        url = "https://api.github.com/graphql"
                        headers = {
                            'Authorization': f'Bearer {token}',
                            'Content-Type': 'application/json'
                        }
                        
                        query = $TQ
                        query(${'$'}owner: String!, ${'$'}repo: String!, ${'$'}pr_number: Int!) {
                          repository(owner: ${'$'}owner, name: ${'$'}repo) {
                            pullRequest(number: ${'$'}pr_number) {
                              closingIssuesReferences(first: 10) {
                                nodes {
                                  number
                                }
                              }
                            }
                          }
                        }
                        $TQ
                        
                        variables = {
                            'owner': owner,
                            'repo': repo,
                            'pr_number': pr_number
                        }
                        
                        try:
                            response = requests.post(url, headers=headers, json={'query': query, 'variables': variables})
                            response.raise_for_status()
                            data = response.json()
                            
                            if 'errors' in data:
                                print(f"⚠ Warning: GraphQL errors: {data['errors']}")
                                return []
                            
                            linked_issues = []
                            pr_data = data.get('data', {}).get('repository', {}).get('pullRequest', {})
                            closing_issues = pr_data.get('closingIssuesReferences', {}).get('nodes', [])
                            
                            for issue in closing_issues:
                                issue_number = issue.get('number')
                                if issue_number:
                                    linked_issues.append(issue_number)
                            
                            return linked_issues
                        except requests.RequestException as e:
                            print(f"⚠ Warning: Could not fetch linked issues via GraphQL API: {e}")
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
                    
                        print(f"Pull Request: #{args.pr_id}")
                        print(f"Target Branch: {args.target_branch}\n")
                    
                        # Step 1: Generate GitHub App installation token
                        token = get_github_app_installation_token()
                    
                        # Step 2: Parse repository from git remote
                        owner, repo = parse_repo_from_git_remote()
                    
                        # Step 3: Configure git credentials with the token
                        configure_git_credentials(token, owner, repo)
                    
                        # Step 4: Get PR details from GitHub API
                        pr_data = get_pr_details(owner, repo, args.pr_id, token)
                        source_branch = pr_data['head']['ref']
                        target_branch = args.target_branch
                    
                        print(f"📋 Source Branch: {source_branch}")
                        print(f"📋 Target Branch: {target_branch}")
                    
                        # Step 5: Validate PR status (not draft, is open)
                        validate_pr_status(pr_data)
                    
                        # Step 6: Validate issue association
                        validate_issue_association(owner, repo, pr_data, token)
                    
                        # Step 7: Validate checks and approvals
                        validate_checks_and_approvals(owner, repo, pr_data, token)
                    
                        # Step 8: Validate branch permissions
                        validate_branch_permissions(owner, repo, target_branch, token)
                    
                        if args.dry_run:
                            print("\n🔍 DRY-RUN: Skipping git operations")
                            print("✓ All validations passed. Integration would proceed in normal mode.")
                            sys.exit(0)
                    
                        # Step 9: Fetch latest changes
                        fetch_branches(source_branch, target_branch)
                    
                        # Step 10: Compare branch heads
                        if compare_branch_heads(source_branch, target_branch):
                            print(f"\n✓ SUCCESS: {source_branch} is already integrated into {target_branch}")
                            print(f"  No action needed - branches are in sync")
                            sys.exit(0)
                    
                        # Step 11: Get Vintage Story version
                        if not args.vs_version:
                            vs_version = get_vs_version(stable=args.api_stable_vs_version)
                        else:
                            vs_version = args.vs_version
                        print(f"\n📦 Vintage Story version: {vs_version}")
                    
                        # Step 12: Determine new version (on target branch context)
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
                    
                    
                        # Step 13: Perform rebase integration
                        perform_rebase_integration(source_branch, target_branch)
                    
                        if not args.dry_run:
                            # Step 14: Push integrated branch and tags
                            push_integrated_branch(target_branch, new_version)
                        else:
                            print("\n🔍 DRY-RUN: Skipping push of integrated branch and tags")
                            print(f"✓ Would push {target_branch} and tag {new_version} in normal mode")
                    
                        # Step 15: Output version for TeamCity and GitHub Actions
                        print(f"\n=== Build Parameters ===")
                        print(f"##teamcity[setParameter name='build.docker.version.new' value='{new_version}']")
                        print(f"##teamcity[setParameter name='build.docker.tag' value='{vs_version}-{new_version}']")
                        print(f"##teamcity[setParameter name='build.version.new' value='{new_version}']")
                        print(f"##teamcity[setParameter name='build.version.old' value='{current_version}']")
                        print(f"##teamcity[setParameter name='build.gameversion' value='{vs_version}']")
                        print(f"##teamcity[setParameter name='build.dryrun' value='{args.dry_run}']")
                    
                        print(f"\n=== ✓{' Dry-Run' if args.dry_run else ''} Integration Complete ===")
                        print(f"✓ Successfully integrated PR #{args.pr_id} ({source_branch} → {target_branch})")
                        print(f"✓ Created version tag: {new_version}")
                        if not args.dry_run:
                            print(f"✓ Pushed changes to origin")
                    
                    
                    if __name__ == '__main__':
                        main()
                """.trimIndent()
                scriptArguments = "--dry-run --pr-id %build.pullrequest.id% --api-stable-vs-version --target-branch main"
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
