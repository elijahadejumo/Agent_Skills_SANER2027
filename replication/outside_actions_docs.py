"""The list of outside actions (Methods, "Outside actions"): writes results/outside_actions.csv with each of
the 140 commands in skillaudit.classes.REMOTE_WRITE, its kind, its tool, and the tool's reference documentation."""
import csv

from skillaudit.classes import REMOTE_WRITE
from skillaudit.paths import RESULTS

DOCS = {
    "git": ("Git", "https://git-scm.com/docs/git-push"),
    "gh": ("GitHub CLI", "https://cli.github.com/manual/"),
    "glab": ("GitLab CLI", "https://docs.gitlab.com/cli/"),
    "kubectl": ("kubectl", "https://kubernetes.io/docs/reference/kubectl/"),
    "vercel": ("Vercel CLI", "https://vercel.com/docs/cli"),
    "helm": ("Helm", "https://helm.sh/docs/helm/"),
    "terraform": ("Terraform", "https://developer.hashicorp.com/terraform/cli/commands"),
    "pulumi": ("Pulumi", "https://www.pulumi.com/docs/iac/cli/commands/"),
    "fly": ("Fly.io flyctl", "https://fly.io/docs/flyctl/"),
    "flyctl": ("Fly.io flyctl", "https://fly.io/docs/flyctl/"),
    "firebase": ("Firebase CLI", "https://firebase.google.com/docs/cli"),
    "wrangler": ("Cloudflare Wrangler", "https://developers.cloudflare.com/workers/wrangler/commands/"),
    "netlify": ("Netlify CLI", "https://cli.netlify.com/"),
    "serverless": ("Serverless Framework", "https://www.serverless.com/framework/docs/providers/aws/cli-reference/deploy"),
    "sam": ("AWS SAM CLI", "https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-cli-command-reference-sam-deploy.html"),
    "cdk": ("AWS CDK CLI", "https://docs.aws.amazon.com/cdk/v2/guide/cli.html"),
    "railway": ("Railway CLI", "https://docs.railway.com/reference/cli-api"),
    "gcloud": ("Google Cloud CLI", "https://cloud.google.com/sdk/gcloud/reference"),
    "npm": ("npm", "https://docs.npmjs.com/cli/commands/npm-publish"),
    "pnpm": ("pnpm", "https://pnpm.io/cli/publish"),
    "yarn": ("Yarn", "https://yarnpkg.com/cli/npm/publish"),
    "bun": ("Bun", "https://bun.sh/docs/cli/publish"),
    "cargo": ("Cargo", "https://doc.rust-lang.org/cargo/commands/cargo-publish.html"),
    "uv": ("uv", "https://docs.astral.sh/uv/guides/package/"),
    "docker": ("Docker", "https://docs.docker.com/reference/cli/docker/image/push/"),
    "./gradlew": ("Gradle", "https://docs.gradle.org/current/userguide/publishing_setup.html"),
    "gradle": ("Gradle", "https://docs.gradle.org/current/userguide/publishing_setup.html"),
    "twine": ("Twine", "https://twine.readthedocs.io/en/stable/"),
    "gem": ("RubyGems", "https://guides.rubygems.org/command-reference/"),
    "poetry": ("Poetry", "https://python-poetry.org/docs/cli/"),
    "prisma": ("Prisma", "https://www.prisma.io/docs/orm/reference/prisma-cli-reference"),
    "supabase": ("Supabase CLI", "https://supabase.com/docs/reference/cli/supabase-db-push"),
    "alembic": ("Alembic", "https://alembic.sqlalchemy.org/en/latest/tutorial.html"),
    "flyway": ("Flyway", "https://documentation.red-gate.com/fd/"),
    "rails": ("Ruby on Rails", "https://guides.rubyonrails.org/active_record_migrations.html"),
    "knex": ("Knex", "https://knexjs.org/guide/migrations.html"),
    "sequelize": ("Sequelize", "https://sequelize.org/docs/v6/other-topics/migrations/"),
    "drizzle-kit": ("Drizzle Kit", "https://orm.drizzle.team/docs/kit-overview"),
    "php": ("Laravel", "https://laravel.com/docs/migrations"),
}
KIND = {"remote_vcs": "code hosting", "deploy": "deploying", "publish": "publishing", "migrate": "migrating"}

if __name__ == "__main__":
    RESULTS.mkdir(parents=True, exist_ok=True)
    with open(RESULTS / "outside_actions.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["command", "kind", "tool", "documentation"])
        for kind, cmds in REMOTE_WRITE.items():
            for c in sorted(cmds):
                tool, url = DOCS[c.split()[0]]
                w.writerow([c, KIND[kind], tool, url])
    tools = {DOCS[c.split()[0]][0] for cmds in REMOTE_WRITE.values() for c in cmds}
    print(f"{sum(map(len, REMOTE_WRITE.values()))} commands from {len(tools)} tools; written: results/outside_actions.csv")
