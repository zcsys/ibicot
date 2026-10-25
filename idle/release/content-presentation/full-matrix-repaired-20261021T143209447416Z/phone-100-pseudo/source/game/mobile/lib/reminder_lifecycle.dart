import 'game_controller.dart';
import 'notification_service.dart';

/// Reminders describe a committed absence. They never advance production and
/// cannot be scheduled by a stale pause after the player has already returned.
class ReminderLifecycle {
  ReminderLifecycle(this.game, this.notifications);
  final GameController game;
  final NotificationService notifications;
  int _generation = 0;
  bool _closed = false;

  Future<void> returned() {
    _generation++;
    return notifications.onReturn();
  }

  Future<void> backgrounded() async {
    final generation = ++_generation;
    game.suspend();
    await game.waitForPendingReplay();
    if (_closed || generation != _generation) return;
    await game.save();
    if (_closed ||
        generation != _generation ||
        !game.hasPersistence ||
        game.saveError != null ||
        game.replaying ||
        game.replayError != null) {
      return;
    }
    await notifications.scheduleForAbsence(
      state: game.state,
      settledThrough: game.settledThrough,
    );
  }

  void close() {
    _closed = true;
    _generation++;
  }
}
