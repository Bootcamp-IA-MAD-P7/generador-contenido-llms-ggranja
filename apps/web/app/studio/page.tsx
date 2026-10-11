import { AuthGate } from "../../components/auth/AuthGate";
import { Workspace } from "../../components/Workspace";

export default function StudioPage() {
  return (
    <AuthGate>
      <Workspace />
    </AuthGate>
  );
}
