import pytest
from app.services.member_service import MemberService
from app.models.member import Member, MemberState
from unittest.mock import MagicMock, call

def test_get_stats():
    # Arrange
    db = MagicMock()
    service = MemberService(db)

    # Mock the chain db.query().group_by().all()
    query_mock = MagicMock()
    group_by_mock = MagicMock()
    all_mock = MagicMock()

    db.query.return_value = query_mock
    query_mock.group_by.return_value = group_by_mock

    # Mock data returned by all()
    group_by_mock.all.return_value = [
        (MemberState.ACTIVE, 10),
        (MemberState.NEW, 5),
        (MemberState.CHURNED, 2)
    ]

    # Act
    stats = service.get_stats()

    # Assert
    assert stats["total"] == 17
    assert stats["active"] == 10
    assert stats["new"] == 5
    assert stats["churned"] == 2
    assert stats["at_risk"] == 0
    assert stats["dormant"] == 0

    # Check retention rate: (10 / 17) * 100 = 58.8
    assert stats["retention_rate"] == 58.8

if __name__ == "__main__":
    pytest.main(["-v", __file__])
